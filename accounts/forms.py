from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password

from core.forms_utils import BootstrapFormMixin

User = get_user_model()

GENDER_CHOICES = [("female", "Female"), ("male", "Male")]


class LoginForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, strip=False)

    def __init__(self, *args, username_label="Email", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = username_label
        self.fields["username"].widget.attrs["placeholder"] = username_label
        self.fields["password"].widget.attrs["placeholder"] = "Password"


class PatientRegistrationForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=255)
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=255)
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, strip=False)
    password_again = forms.CharField(widget=forms.PasswordInput, label="Password again", strip=False)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if len(email) > 150:
            raise forms.ValidationError("Email must be 150 characters or fewer.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean(self):
        data = super().clean()
        pw, pw2 = data.get("password"), data.get("password_again")
        if pw and pw2 and pw != pw2:
            self.add_error("password_again", "Password and Confirm Password fields do not match.")
        elif pw:
            candidate = User(email=data.get("email") or "", full_name=data.get("full_name", ""))
            try:
                validate_password(pw, candidate)
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return data

    def save(self):
        d = self.cleaned_data
        return User.objects.create_user(
            username=d["email"], email=d["email"], password=d["password"],
            role="patient", full_name=d["full_name"], address=d["address"],
            city=d["city"], gender=d["gender"],
        )


class PortalPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    """Django's password-change form with the labels used by the original UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Current Password"
        self.fields["new_password1"].label = "New Password"
        self.fields["new_password2"].label = "Confirm Password"
        self.fields["new_password1"].help_text = ""
