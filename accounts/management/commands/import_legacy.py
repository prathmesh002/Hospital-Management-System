"""
Import data from the original PHP/MySQL `hms` database.

    python manage.py import_legacy --host localhost --user root --password "" --database hms
    python manage.py import_legacy --sqlite /path/to/copy_of_legacy.sqlite     # e.g. a converted dump

Notes
* Old MD5 password hashes are kept as-is (hasher `legacy_md5`) and are silently
  upgraded to PBKDF2 when each person next logs in. The old admin password was
  stored in plain text, so it is hashed properly here.
* Column names were inferred from the PHP source (there was no SQL file in the
  project). Missing/renamed date columns fall back to "now". Session logs
  (userlog / doctorslog) are NOT imported.
* Run it against an empty database; rows whose e-mail already exists are skipped.
"""
import re
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (Appointment, ContactQuery, Doctor, MedicalHistory, PatientRecord, SitePage,
                         Specialization)

User = get_user_model()
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def parse_dt(value):
    if not value:
        return timezone.now()
    if isinstance(value, datetime):
        dt = value
    else:
        dt = None
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d", "%d-%m-%Y %I:%M:%S %p"):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            return timezone.now()
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def parse_date(value):
    return parse_dt(value).date()


def parse_time(value):
    text = str(value or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return datetime.min.time()


def money(value):
    try:
        return Decimal(str(value).strip() or "0")
    except InvalidOperation:
        return Decimal("0")


def truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes")


class Command(BaseCommand):
    help = "Import users, doctors, patients, appointments and content from the legacy PHP/MySQL database."

    def add_arguments(self, parser):
        parser.add_argument("--sqlite", help="Path to a SQLite copy of the legacy database")
        parser.add_argument("--host", default="localhost")
        parser.add_argument("--port", type=int, default=3306)
        parser.add_argument("--user", default="root")
        parser.add_argument("--password", default="")
        parser.add_argument("--database", default="hms")

    # -- data access -----------------------------------------------------
    def connect(self, o):
        if o["sqlite"]:
            conn = sqlite3.connect(o["sqlite"])
            conn.row_factory = sqlite3.Row
            return conn
        try:
            import pymysql
        except ImportError:
            raise CommandError("Install PyMySQL (pip install PyMySQL) or use --sqlite.")
        return pymysql.connect(host=o["host"], port=o["port"], user=o["user"], password=o["password"],
                               database=o["database"], charset="utf8mb4")

    def rows(self, conn, table):
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM %s" % table)
        except Exception:
            self.stdout.write(self.style.WARNING("  table %s not found - skipped" % table))
            return []
        cols = [c[0].lower() for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    @staticmethod
    def set_legacy_password(user, raw):
        raw = (raw or "").strip()
        if MD5_RE.match(raw):
            user.password = "legacy_md5$$" + raw.lower()
        elif raw:
            user.set_password(raw)
        else:
            user.set_unusable_password()

    # -- import ------------------------------------------------------------
    @transaction.atomic
    def handle(self, *args, **o):
        conn = self.connect(o)
        spec_map, doctor_map, user_map, patient_map = {}, {}, {}, {}
        skipped = 0

        for r in self.rows(conn, "admin"):
            if User.objects.filter(username=r["username"]).exists():
                continue
            u = User(username=r["username"], role="admin", is_staff=True, is_superuser=True, full_name="Administrator")
            if r.get("password"):
                u.set_password(str(r["password"]))
            else:
                u.set_unusable_password()
            u.save()

        for r in self.rows(conn, "doctorspecilization"):
            name = (r.get("specilization") or "").strip()
            if name:
                spec_map[name] = Specialization.objects.get_or_create(name=name)[0]
                spec_map[r["id"]] = spec_map[name]

        for r in self.rows(conn, "users"):
            email = (r.get("email") or "").strip().lower()
            if not email or User.objects.filter(email=email).exists():
                skipped += 1
                continue
            u = User(username=email, email=email, role="patient", full_name=r.get("fullname") or "",
                     address=r.get("address") or "", city=r.get("city") or "", gender=r.get("gender") or "",
                     date_joined=parse_dt(r.get("regdate")))
            self.set_legacy_password(u, r.get("password"))
            u.save()
            user_map[r["id"]] = u

        for r in self.rows(conn, "doctors"):
            email = (r.get("docemail") or "").strip().lower()
            spec_name = (r.get("specilization") or "").strip() or "General"
            if not email or User.objects.filter(email=email).exists():
                skipped += 1
                continue
            spec = spec_map.get(spec_name) or Specialization.objects.get_or_create(name=spec_name)[0]
            u = User(username=email, email=email, role="doctor", full_name=r.get("doctorname") or "",
                     date_joined=parse_dt(r.get("creationdate")))
            self.set_legacy_password(u, r.get("password"))
            u.save()
            doctor_map[r["id"]] = Doctor.objects.create(
                user=u, specialization=spec, address=r.get("address") or "", fees=money(r.get("docfees")),
                contact_no=str(r.get("contactno") or ""))

        for r in self.rows(conn, "tblpatient"):
            rec = PatientRecord.objects.create(
                doctor=doctor_map.get(r.get("docid")), name=r.get("patientname") or "",
                contact_no=str(r.get("patientcontno") or ""), email=(r.get("patientemail") or "").lower(),
                gender=r.get("patientgender") or "", address=r.get("patientadd") or "",
                age=str(r.get("patientage") or ""), medical_history=r.get("patientmedhis") or "")
            patient_map[r["id"]] = rec
            created = parse_dt(r.get("creationdate"))
            PatientRecord.objects.filter(pk=rec.pk).update(created_at=created)

        for r in self.rows(conn, "tblmedicalhistory"):
            rec = patient_map.get(r.get("patientid"))
            if rec is None:
                continue
            h = MedicalHistory.objects.create(
                patient=rec, blood_pressure=r.get("bloodpressure") or "", blood_sugar=r.get("bloodsugar") or "",
                weight=r.get("weight") or "", temperature=r.get("temperature") or "",
                prescription=r.get("medicalpres") or "")
            MedicalHistory.objects.filter(pk=h.pk).update(created_at=parse_dt(r.get("creationdate")))

        for r in self.rows(conn, "appointment"):
            doctor, patient = doctor_map.get(r.get("doctorid")), user_map.get(r.get("userid"))
            if doctor is None or patient is None:
                skipped += 1
                continue
            Appointment.objects.create(
                doctor=doctor, patient=patient, specialization=r.get("doctorspecialization") or doctor.specialization.name,
                fees=money(r.get("consultancyfees")), appointment_date=parse_date(r.get("appointmentdate")),
                appointment_time=parse_time(r.get("appointmenttime")), user_status=truthy(r.get("userstatus")),
                doctor_status=truthy(r.get("doctorstatus")), posted_at=parse_dt(r.get("postingdate")))

        for r in self.rows(conn, "tblcontactus"):
            q = ContactQuery.objects.create(
                full_name=r.get("fullname") or "", email=r.get("email") or "", contact_no=str(r.get("contactno") or ""),
                message=r.get("message") or "", admin_remark=r.get("adminremark") or "",
                is_read=truthy(r.get("isread")),
                remark_updated_at=parse_dt(r["lastupdationdate"]) if r.get("lastupdationdate") else None)
            ContactQuery.objects.filter(pk=q.pk).update(posted_at=parse_dt(r.get("postingdate")))

        for r in self.rows(conn, "tblpage"):
            ptype = (r.get("pagetype") or "").strip()
            if ptype in (SitePage.ABOUT, SitePage.CONTACT):
                SitePage.objects.update_or_create(page_type=ptype, defaults=dict(
                    title=r.get("pagetitle") or "", description=r.get("pagedescription") or "",
                    email=r.get("email") or "", mobile_number=str(r.get("mobilenumber") or ""),
                    opening_time=r.get("openningtime") or ""))

        self.stdout.write(self.style.SUCCESS(
            "Imported %d patients, %d doctors, %d patient files (%d rows skipped)."
            % (len(user_map), len(doctor_map), len(patient_map), skipped)))
