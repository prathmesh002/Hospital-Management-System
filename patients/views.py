from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import patient_required
from accounts.views import change_password
from core.models import Appointment, Doctor, PatientRecord, Specialization

from .forms import AppointmentForm, EmailChangeForm, ProfileForm


@patient_required
def dashboard(request):
    return render(request, "patients/dashboard.html")


@patient_required
def book_appointment(request):
    form = AppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        doctor = d["doctor"]
        Appointment.objects.create(
            doctor=doctor, patient=request.user,
            specialization=doctor.specialization.name, fees=doctor.fees,   # fees come from the DB, not the browser
            appointment_date=d["appointment_date"], appointment_time=d["appointment_time"],
        )
        messages.success(request, "Your appointment was successfully booked.")
        return redirect("patients:appointment_history")
    return render(request, "patients/book_appointment.html", {
        "form": form,
        "specializations": Specialization.objects.all(),
        "doctors": Doctor.objects.select_related("user", "specialization"),
        "selected_doctor": request.POST.get("doctor", ""),
        "selected_specialization": request.POST.get("specialization", ""),
    })


@patient_required
def appointment_history(request):
    appts = Appointment.objects.filter(patient=request.user).select_related("doctor__user")
    return render(request, "patients/appointment_history.html", {"appointments": appts})


@patient_required
@require_POST
def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, patient=request.user)
    appt.user_status = False
    appt.save(update_fields=["user_status", "updated_at"])
    messages.success(request, "Your appointment was cancelled.")
    return redirect("patients:appointment_history")


def _own_records(user):
    # Patient files are linked to a login by matching e-mail (same rule as the PHP app).
    return PatientRecord.objects.filter(email__iexact=user.email or "")


@patient_required
def medical_history_list(request):
    return render(request, "patients/medical_history_list.html", {"records": _own_records(request.user)})


@patient_required
def medical_history_detail(request, pk):
    record = get_object_or_404(_own_records(request.user), pk=pk)   # patients can only open their own file
    return render(request, "patients/medical_history_detail.html",
                  {"record": record, "history": record.history.all()})


@patient_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was updated successfully.")
        return redirect("patients:edit_profile")
    return render(request, "patients/edit_profile.html", {"form": form})


@patient_required
def change_email(request):
    form = EmailChangeForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        user, new_email = request.user, form.cleaned_data["email"]
        old_email = (user.email or "").lower()
        with transaction.atomic():
            user.email = new_email
            if user.username.lower() == old_email:      # username was the old e-mail: keep them equal
                user.username = new_email
            user.save()
            if old_email:                               # patient files are linked by e-mail: keep the link
                PatientRecord.objects.filter(email__iexact=old_email).update(email=new_email)
        messages.success(request, "Your email was updated successfully.")
        return redirect("patients:edit_profile")
    return render(request, "patients/change_email.html", {"form": form})


@patient_required
def change_password_view(request):
    return change_password(request, "patients/change_password.html", "patients:dashboard")
