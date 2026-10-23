from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse


def role_required(role, login_url_name):
    """Allow only authenticated users with `role`; others go to that role's login page."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or user.role != role:
                return redirect_to_login(request.get_full_path(), reverse(login_url_name))
            if role == "doctor" and not hasattr(user, "doctor_profile"):
                # A user with the doctor role but no Doctor profile (e.g. created in /django-admin/)
                # would crash every doctor page; sign them out with an explanation instead.
                logout(request)
                messages.error(request, "Your doctor profile has not been set up yet. Please contact the administrator.")
                return redirect(login_url_name)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


patient_required = role_required("patient", "accounts:patient_login")
doctor_required = role_required("doctor", "accounts:doctor_login")
admin_required = role_required("admin", "accounts:admin_login")
