from django import forms

from .forms_utils import BootstrapFormMixin
from .models import ContactQuery, MedicalHistory, PatientRecord


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactQuery
        fields = ["full_name", "email", "contact_no", "message"]


class PatientRecordForm(BootstrapFormMixin, forms.ModelForm):
    """Used by doctors to add/edit a patient file."""

    class Meta:
        model = PatientRecord
        fields = ["name", "contact_no", "email", "gender", "address", "age", "medical_history"]
        labels = {
            "name": "Patient Name", "contact_no": "Patient Contact No", "email": "Patient Email",
            "gender": "Gender", "address": "Patient Address", "age": "Patient Age",
            "medical_history": "Patient Medical History (if any)",
        }
        widgets = {
            "gender": forms.RadioSelect(choices=[("female", "Female"), ("male", "Male")]),
            "address": forms.Textarea(attrs={"rows": 3}),
            "medical_history": forms.Textarea(attrs={"rows": 4}),
            "contact_no": forms.TextInput(attrs={"maxlength": 10, "pattern": "[0-9]+"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = PatientRecord.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A patient with this email already exists.")
        return email


class MedicalHistoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ["blood_pressure", "blood_sugar", "weight", "temperature", "prescription"]
        labels = {
            "blood_pressure": "Blood Pressure", "blood_sugar": "Blood Sugar", "weight": "Weight",
            "temperature": "Body Temperature", "prescription": "Medical Prescription",
        }
        widgets = {"prescription": forms.Textarea(attrs={"rows": 6})}
