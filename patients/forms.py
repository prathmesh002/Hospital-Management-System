from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.forms import GENDER_CHOICES
from core.forms_utils import BootstrapFormMixin
from core.models import Appointment, Doctor, Specialization

User = get_user_model()


class AppointmentForm(BootstrapFormMixin, forms.Form):
    specialization = forms.ModelChoiceField(Specialization.objects.all(), empty_label="Select Specialization",
                                            label="Doctor Specialization")
    doctor = forms.ModelChoiceField(Doctor.objects.select_related("user", "specialization"),
                                    empty_label="Select Doctor", label="Doctors")
    appointment_date = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}))
    appointment_time = forms.TimeField(label="Time", widget=forms.TimeInput(attrs={"type": "time"}))

    def clean(self):
        data = super().clean()
        spec, doctor = data.get("specialization"), data.get("doctor")
        day, when = data.get("appointment_date"), data.get("appointment_time")
        if spec and doctor and doctor.specialization_id != spec.pk:
            self.add_error("doctor", "This doctor does not belong to the selected specialization.")
        if day and day < timezone.localdate():
            self.add_error("appointment_date", "Appointment date cannot be in the past.")
        elif day and when and day == timezone.localdate() and when <= timezone.localtime().time():
            self.add_error("appointment_time", "That time has already passed today.")
        if doctor and day and when:
            clash = Appointment.objects.filter(doctor=doctor, appointment_date=day, appointment_time=when,
                                               user_status=True, doctor_status=True).exists()
            if clash:
                self.add_error("appointment_time", "The doctor already has an appointment at that time.")
        return data


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "address", "city", "gender"]
        labels = {"full_name": "User Name", "address": "Address", "city": "City", "gender": "Gender"}
        widgets = {"address": forms.Textarea(attrs={"rows": 3}),
                   "gender": forms.Select(choices=[("", "Select"), *GENDER_CHOICES])}


class EmailChangeForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label="New Email")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if len(email) > 150:
            raise forms.ValidationError("Email must be 150 characters or fewer.")
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Email already exists.")
        return email
