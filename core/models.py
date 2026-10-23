from django.conf import settings
from django.db import models
from django.utils import timezone


class Specialization(models.Model):
    """PHP table: doctorSpecilization."""

    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Doctor profile. Login/identity (name, e-mail, password) lives on the linked User."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="doctors")
    address = models.TextField("Clinic address")
    fees = models.DecimalField("Consultancy fees", max_digits=10, decimal_places=2)
    contact_no = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    @property
    def name(self):
        return self.user.display_name

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.name


class PatientRecord(models.Model):
    """A patient file kept by doctors. PHP table: tblpatient."""

    doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.SET_NULL, related_name="patient_records")
    name = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=20)
    email = models.EmailField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    age = models.CharField(max_length=10)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class MedicalHistory(models.Model):
    """One visit entry for a PatientRecord. PHP table: tblmedicalhistory."""

    patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name="history")
    blood_pressure = models.CharField(max_length=100)
    blood_sugar = models.CharField(max_length=100)
    weight = models.CharField(max_length=100)
    temperature = models.CharField(max_length=100)
    prescription = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "medical history"


class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    # Snapshots taken at booking time (a doctor may later change specialty/fees)
    specialization = models.CharField(max_length=255)
    fees = models.DecimalField("Consultancy fees", max_digits=10, decimal_places=2)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    user_status = models.BooleanField("active for patient", default=True)
    doctor_status = models.BooleanField("active for doctor", default=True)
    posted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    @property
    def is_active(self):
        return self.user_status and self.doctor_status

    def status_for(self, viewer):
        """Status text as shown to 'patient', 'doctor' or 'admin' (same wording as the PHP app)."""
        if self.is_active:
            return "Active"
        if not self.user_status and self.doctor_status:
            return {"patient": "Cancel by You"}.get(viewer, "Cancel by Patient")
        if self.user_status and not self.doctor_status:
            return {"doctor": "Cancel by you"}.get(viewer, "Cancel by Doctor")
        return "Cancelled"

    @property
    def patient_status(self):
        return self.status_for("patient")

    @property
    def doctor_view_status(self):
        return self.status_for("doctor")

    @property
    def admin_status(self):
        return self.status_for("admin")


class ContactQuery(models.Model):
    """Public contact-form message. PHP table: tblcontactus."""

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    contact_no = models.CharField(max_length=20)
    message = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)
    admin_remark = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    remark_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "contact queries"


class SitePage(models.Model):
    """Editable 'About us' / 'Contact us' content. PHP table: tblpage."""

    ABOUT = "aboutus"
    CONTACT = "contactus"
    PAGE_TYPES = [(ABOUT, "About us"), (CONTACT, "Contact us")]

    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, unique=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
    opening_time = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.get_page_type_display()

    @classmethod
    def get_page(cls, page_type):
        return cls.objects.get_or_create(page_type=page_type)[0]
