from django import forms
from django.contrib.auth import get_user_model

from core.forms_utils import BootstrapFormMixin
from core.models import Doctor, Specialization

User = get_user_model()


class DoctorProfileForm(BootstrapFormMixin, forms.Form):
    """Edit a doctor's own profile (doctor portal) or any doctor (admin portal)."""

    specialization = forms.ModelChoiceField(Specialization.objects.all(), empty_label="Select Specialization",
                                            label="Doctor Specialization")
    full_name = forms.CharField(max_length=255, label="Doctor Name")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Doctor Clinic Address")
    fees = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2, label="Doctor Consultancy Fees")
    contact_no = forms.CharField(max_length=20, label="Doctor Contact No")
    email = forms.EmailField(label="Doctor Email")

    def __init__(self, *args, doctor=None, email_editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctor = doctor
        if doctor is not None:
            self.initial.update(
                specialization=doctor.specialization_id, full_name=doctor.user.full_name,
                address=doctor.address, fees=doctor.fees, contact_no=doctor.contact_no,
                email=doctor.user.email,
            )
        if not email_editable:
            self.fields["email"].disabled = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if len(email) > 150:
            raise forms.ValidationError("Email must be 150 characters or fewer.")
        qs = User.objects.filter(email__iexact=email)
        if self.doctor is not None:
            qs = qs.exclude(pk=self.doctor.user_id)
        if qs.exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def save(self):
        d, doctor = self.cleaned_data, self.doctor
        user = doctor.user
        user.full_name = d["full_name"]
        user.email = d["email"]
        user.username = d["email"]
        user.save()
        doctor.specialization = d["specialization"]
        doctor.address = d["address"]
        doctor.fees = d["fees"]
        doctor.contact_no = d["contact_no"]
        doctor.save()
        return doctor
