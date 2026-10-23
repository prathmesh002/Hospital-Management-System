import hashlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import LoginLog
from core.models import Appointment, Doctor, PatientRecord, Specialization

User = get_user_model()
PW = "Str0ng-Pass!42"


class HmsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spec = Specialization.objects.create(name="Cardiology")
        du = User.objects.create_user("doc@x.com", "doc@x.com", PW, role="doctor", full_name="Dr X")
        cls.doctor = Doctor.objects.create(user=du, specialization=cls.spec, address="Clinic", fees=300, contact_no="123")
        cls.patient = User.objects.create_user("pat@x.com", "pat@x.com", PW, role="patient", full_name="Pat")
        cls.other = User.objects.create_user("other@x.com", "other@x.com", PW, role="patient", full_name="Other")
        cls.admin = User.objects.create_user("admin", password=PW, role="admin", is_staff=True, is_superuser=True)

    def book_payload(self, days=2, time="10:30"):
        return {"specialization": self.spec.pk, "doctor": self.doctor.pk,
                "appointment_date": (timezone.localdate() + timedelta(days=days)).isoformat(),
                "appointment_time": time}


class AuthTests(HmsTestCase):
    def test_legacy_md5_password_works_and_is_upgraded(self):
        u = User.objects.create_user("old@x.com", "old@x.com", role="patient")
        u.password = "legacy_md5$$" + hashlib.md5(b"secret").hexdigest()
        u.save()
        self.assertTrue(u.check_password("secret"))
        u.refresh_from_db()
        self.assertTrue(u.password.startswith("pbkdf2_sha256$"))

    def test_patient_login_logs_session_and_redirects(self):
        r = self.client.post(reverse("accounts:patient_login"), {"username": "pat@x.com", "password": PW})
        self.assertRedirects(r, reverse("patients:dashboard"))
        self.assertTrue(LoginLog.objects.filter(username="pat@x.com", role="patient", status=True).exists())
        self.client.get(reverse("accounts:logout"))
        self.assertIsNotNone(LoginLog.objects.get(username="pat@x.com", status=True).logout_time)

    def test_wrong_role_cannot_use_other_portal_login(self):
        r = self.client.post(reverse("accounts:patient_login"), {"username": "doc@x.com", "password": PW})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(LoginLog.objects.filter(username="doc@x.com", status=False).exists())

    def test_admin_logs_in_with_username(self):
        r = self.client.post(reverse("accounts:admin_login"), {"username": "admin", "password": PW})
        self.assertRedirects(r, reverse("adminpanel:dashboard"))

    def test_portals_require_the_right_role(self):
        self.assertEqual(self.client.get(reverse("patients:dashboard")).status_code, 302)
        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(reverse("adminpanel:dashboard")).status_code, 302)
        self.assertEqual(self.client.get(reverse("doctors:dashboard")).status_code, 302)
        self.assertEqual(self.client.get(reverse("patients:dashboard")).status_code, 200)

    def test_registration_creates_patient(self):
        r = self.client.post(reverse("accounts:register"), {
            "full_name": "New Person", "address": "x", "city": "y", "gender": "female",
            "email": "new@x.com", "password": PW, "password_again": PW})
        self.assertRedirects(r, reverse("accounts:patient_login"))
        self.assertEqual(User.objects.get(email="new@x.com").role, "patient")


class AppointmentTests(HmsTestCase):
    def test_booking_uses_database_fee_and_blocks_double_booking(self):
        self.client.force_login(self.patient)
        r = self.client.post(reverse("patients:book_appointment"), self.book_payload())
        self.assertRedirects(r, reverse("patients:appointment_history"))
        appt = Appointment.objects.get()
        self.assertEqual(appt.fees, 300)
        self.assertEqual(appt.patient_status, "Active")

        self.client.force_login(self.other)
        r = self.client.post(reverse("patients:book_appointment"), self.book_payload())
        self.assertEqual(r.status_code, 200)           # re-rendered with an error
        self.assertEqual(Appointment.objects.count(), 1)

    def test_past_date_rejected(self):
        self.client.force_login(self.patient)
        self.client.post(reverse("patients:book_appointment"), self.book_payload(days=-1))
        self.assertEqual(Appointment.objects.count(), 0)

    def test_cancel_flows_and_ownership(self):
        appt = Appointment.objects.create(doctor=self.doctor, patient=self.patient, specialization="Cardiology",
                                          fees=300, appointment_date=timezone.localdate() + timedelta(days=1),
                                          appointment_time="09:00")
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("patients:cancel_appointment", args=[appt.pk])).status_code, 404)
        self.client.force_login(self.patient)
        self.client.post(reverse("patients:cancel_appointment", args=[appt.pk]))
        appt.refresh_from_db()
        self.assertFalse(appt.user_status)
        self.assertEqual(appt.patient_status, "Cancel by You")
        self.assertEqual(appt.admin_status, "Cancel by Patient")

    def test_doctor_cancel(self):
        appt = Appointment.objects.create(doctor=self.doctor, patient=self.patient, specialization="Cardiology",
                                          fees=300, appointment_date=timezone.localdate() + timedelta(days=1),
                                          appointment_time="09:00")
        self.client.force_login(self.doctor.user)
        self.client.post(reverse("doctors:cancel_appointment", args=[appt.pk]))
        appt.refresh_from_db()
        self.assertEqual(appt.patient_status, "Cancel by Doctor")


class PatientRecordTests(HmsTestCase):
    def setUp(self):
        self.record = PatientRecord.objects.create(
            doctor=self.doctor, name="Pat", contact_no="9", email="pat@x.com", gender="male",
            address="a", age="30")

    def test_patient_sees_only_own_medical_history(self):
        url = reverse("patients:medical_history_detail", args=[self.record.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_doctor_adds_history_entry(self):
        self.client.force_login(self.doctor.user)
        r = self.client.post(reverse("doctors:view_patient", args=[self.record.pk]), {
            "blood_pressure": "120/80", "blood_sugar": "90", "weight": "70", "temperature": "98.6",
            "prescription": "Rest"})
        self.assertRedirects(r, reverse("doctors:view_patient", args=[self.record.pk]))
        self.assertEqual(self.record.history.count(), 1)

    def test_admin_search_and_dashboard(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("adminpanel:dashboard")).status_code, 200)
        r = self.client.post(reverse("adminpanel:patient_search"), {"searchdata": "Pat"})
        self.assertContains(r, "Pat")


class RegressionTests(HmsTestCase):
    def test_changing_email_keeps_username_and_patient_file_linked(self):
        record = PatientRecord.objects.create(
            doctor=self.doctor, name="Pat", contact_no="9", email="pat@x.com", gender="male",
            address="a", age="30")
        self.client.force_login(self.patient)
        self.client.post(reverse("patients:change_email"), {"email": "New@X.com"})
        self.patient.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(self.patient.email, "new@x.com")
        self.assertEqual(self.patient.username, "new@x.com")
        self.assertEqual(record.email, "new@x.com")

    def test_doctor_role_without_profile_is_signed_out_instead_of_crashing(self):
        user = User.objects.create_user("nodoc@x.com", "nodoc@x.com", PW, role="doctor")
        self.client.force_login(user)
        r = self.client.get(reverse("doctors:dashboard"))
        self.assertRedirects(r, reverse("accounts:doctor_login"))

    def test_time_earlier_today_is_rejected(self):
        now = timezone.localtime()
        if now.hour == 0:
            self.skipTest("no earlier time today to test with")
        earlier = (now - timedelta(hours=1)).strftime("%H:%M")
        self.client.force_login(self.patient)
        r = self.client.post(reverse("patients:book_appointment"), self.book_payload(days=0, time=earlier))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 0)
