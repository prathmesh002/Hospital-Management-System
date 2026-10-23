from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_GET

from django.contrib.auth import authenticate, get_user_model

from .forms import LoginForm, PatientRegistrationForm, PortalPasswordChangeForm
from .models import LoginLog

User = get_user_model()

LOG_SESSION_KEY = "hms_login_log_id"


def client_ip(request):
    return request.META.get("REMOTE_ADDR") or None


class RoleLoginView(View):
    """Shared login logic for the patient, doctor and admin portals (with session logging)."""

    role = None
    template_name = "accounts/login.html"
    heading = ""
    username_label = "Email"
    dashboard_url = ""
    show_register = False
    show_forgot = True

    def _render(self, request, form, status=200):
        ctx = {
            "form": form, "heading": self.heading, "role": self.role,
            "show_register": self.show_register, "show_forgot": self.show_forgot,
            "next": request.POST.get("next") or request.GET.get("next", ""),
        }
        return render(request, self.template_name, ctx, status=status)

    def get(self, request):
        if request.user.is_authenticated and request.user.role == self.role:
            return redirect(self.dashboard_url)
        return self._render(request, LoginForm(username_label=self.username_label))

    def post(self, request):
        form = LoginForm(request.POST, username_label=self.username_label)
        if not form.is_valid():
            return self._render(request, form)
        username = form.cleaned_data["username"].strip()
        user = authenticate(request, username=username, password=form.cleaned_data["password"])
        if user is not None and user.role == self.role:
            login(request, user)
            log = LoginLog.objects.create(user=user, role=self.role, username=username,
                                          ip=client_ip(request), status=True)
            request.session[LOG_SESSION_KEY] = log.pk
            target = request.POST.get("next", "")
            if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
                return redirect(target)
            return redirect(self.dashboard_url)
        LoginLog.objects.create(user=None, role=self.role, username=username,
                                ip=client_ip(request), status=False)
        messages.error(request, "Invalid username or password.")
        return self._render(request, form, status=200)


class PatientLoginView(RoleLoginView):
    role = "patient"
    heading = "HMS | Patient Login"
    dashboard_url = "patients:dashboard"
    show_register = True


class DoctorLoginView(RoleLoginView):
    role = "doctor"
    heading = "HMS | Doctor Login"
    dashboard_url = "doctors:dashboard"


class AdminLoginView(RoleLoginView):
    role = "admin"
    heading = "HMS | Admin Login"
    username_label = "Username"
    dashboard_url = "adminpanel:dashboard"
    show_forgot = False


def logout_view(request):
    """Records the logout time, ends the session and returns to the landing page."""
    log_id = request.session.get(LOG_SESSION_KEY)
    if request.user.is_authenticated and log_id:
        LoginLog.objects.filter(pk=log_id, logout_time__isnull=True).update(logout_time=timezone.now())
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("core:index")


def register_view(request):
    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully registered. You can log in now.")
            return redirect("accounts:patient_login")
    else:
        form = PatientRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@require_GET
def check_email(request):
    """AJAX: is this e-mail free for patient registration? (replaces check_availability.php)"""
    email = request.GET.get("email", "").strip()
    taken = bool(email) and User.objects.filter(email__iexact=email).exists()
    return JsonResponse({"available": not taken})


# ---- password reset: Django's token-by-email flow replaces the PHP
# "enter your name + email and set a new password" page, which let anyone who
# knew a person's name and email take over their account. -----------------
class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


def change_password(request, template, home_url, form_cls=PortalPasswordChangeForm, extra=None):
    """Helper used by the three portals' change-password views."""
    if request.method == "POST":
        form = form_cls(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect(request.path)
        messages.error(request, "Please correct the errors below.")
    else:
        form = form_cls(request.user)
    ctx = {"form": form}
    ctx.update(extra or {})
    return render(request, template, ctx)
