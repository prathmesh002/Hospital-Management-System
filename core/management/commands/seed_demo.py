"""Creates demo data so every portal can be tried straight away:  python manage.py seed_demo"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Appointment, Doctor, PatientRecord, SitePage, Specialization

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo specializations, an admin, a doctor, a patient and sample content (DEMO ONLY)."

    def handle(self, *args, **options):
        specs = [Specialization.objects.get_or_create(name=n)[0]
                 for n in ["General Physician", "Cardiology", "Dermatology", "Pediatrics", "Orthopedics"]]

        if not User.objects.filter(username="admin").exists():
            User.objects.create_user("admin", password="Admin@12345", role="admin", full_name="Administrator",
                                     is_staff=True, is_superuser=True)

        if not User.objects.filter(email="doctor@example.com").exists():
            u = User.objects.create_user("doctor@example.com", "doctor@example.com", "Doctor@12345",
                                         role="doctor", full_name="Dr. Asha Rao")
            Doctor.objects.create(user=u, specialization=specs[0], address="12 Clinic Road, Hyderabad",
                                  fees=500, contact_no="9876543210")

        if not User.objects.filter(email="patient@example.com").exists():
            User.objects.create_user("patient@example.com", "patient@example.com", "Patient@12345",
                                     role="patient", full_name="Ravi Kumar", address="45 Lake View",
                                     city="Hyderabad", gender="male")

        doctor = Doctor.objects.first()
        patient = User.objects.get(email="patient@example.com")
        if not Appointment.objects.exists():
            Appointment.objects.create(doctor=doctor, patient=patient, specialization=doctor.specialization.name,
                                       fees=doctor.fees, appointment_date=timezone.localdate() + timedelta(days=3),
                                       appointment_time="10:30")
        if not PatientRecord.objects.exists():
            PatientRecord.objects.create(doctor=doctor, name="Ravi Kumar", contact_no="9000000001",
                                         email="patient@example.com", gender="male", address="45 Lake View",
                                         age="34", medical_history="No known allergies.")

        about = SitePage.get_page(SitePage.ABOUT)
        if not about.description:
            about.title, about.description = "About Us", "Our hospital provides compassionate, round-the-clock care."
            about.save()
        contact = SitePage.get_page(SitePage.CONTACT)
        if not contact.description:
            contact.title, contact.description = "Contact Us", "Hospital Road, Hyderabad, Telangana"
            contact.email, contact.mobile_number, contact.opening_time = "info@example.com", "9876543210", "Mon-Sat 9am-6pm"
            contact.save()

        self.stdout.write(self.style.SUCCESS("Demo data ready. These are DEMO credentials - do not use in production:"))
        self.stdout.write("  Admin   : /hms/admin/login/   admin / Admin@12345")
        self.stdout.write("  Doctor  : /hms/doctor/login/  doctor@example.com / Doctor@12345")
        self.stdout.write("  Patient : /hms/login/         patient@example.com / Patient@12345")
