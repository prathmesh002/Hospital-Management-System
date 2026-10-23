from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from core.forms_utils import BootstrapFormMixin
from core.models import ContactQuery, SitePage, Specialization
from doctors.forms import DoctorProfileForm

User = get_user_model()


class AddDoctorForm(DoctorProfileForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password", strip=False)
    password_again = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", strip=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("doctor", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        pw, pw2 = data.get("password"), data.get("password_again")
        if pw and pw2 and pw != pw2:
            self.add_error("password_again", "Password and Confirm Password fields do not match.")
        elif pw:
            try:
                validate_password(pw, User(email=data.get("email") or "", full_name=data.get("full_name", "")))
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return data

    def save(self):
        from core.models import Doctor

        d = self.cleaned_data
        user = User.objects.create_user(username=d["email"], email=d["email"], password=d["password"],
                                        role="doctor", full_name=d["full_name"])
        return Doctor.objects.create(user=user, specialization=d["specialization"], address=d["address"],
                                     fees=d["fees"], contact_no=d["contact_no"])


class SpecializationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Specialization
        fields = ["name"]
        labels = {"name": "Doctor Specialization"}
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Enter Doctor Specialization"})}


class QueryRemarkForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ContactQuery
        fields = ["admin_remark"]
        labels = {"admin_remark": "Admin Remark"}
        widgets = {"admin_remark": forms.Textarea(attrs={"rows": 5})}


class AboutPageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SitePage
        fields = ["title", "description"]
        labels = {"title": "Page Title", "description": "Page Description"}
        widgets = {"description": forms.Textarea(attrs={"rows": 10})}


class ContactPageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SitePage
        fields = ["title", "description", "email", "mobile_number", "opening_time"]
        labels = {"title": "Page Title", "description": "Page Description", "email": "Email",
                  "mobile_number": "Mobile Number", "opening_time": "Opening Time"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class DateRangeForm(BootstrapFormMixin, forms.Form):
    from_date = forms.DateField(label="From Date", widget=forms.DateInput(attrs={"type": "date"}))
    to_date = forms.DateField(label="To Date", widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        data = super().clean()
        if data.get("from_date") and data.get("to_date") and data["from_date"] > data["to_date"]:
            raise forms.ValidationError("'From Date' must not be after 'To Date'.")
        return data
