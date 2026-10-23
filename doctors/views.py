from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import doctor_required
from accounts.views import change_password
from core.forms import MedicalHistoryForm, PatientRecordForm
from core.models import Appointment, PatientRecord

from .forms import DoctorProfileForm


@doctor_required
def dashboard(request):
    return render(request, "doctors/dashboard.html")


@doctor_required
def appointment_history(request):
    appts = Appointment.objects.filter(doctor=request.user.doctor_profile).select_related("patient")
    return render(request, "doctors/appointment_history.html", {"appointments": appts})


@doctor_required
@require_POST
def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, doctor=request.user.doctor_profile)
    appt.doctor_status = False
    appt.save(update_fields=["doctor_status", "updated_at"])
    messages.success(request, "Appointment cancelled.")
    return redirect("doctors:appointment_history")


@doctor_required
def add_patient(request):
    form = PatientRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.doctor = request.user.doctor_profile
        record.save()
        messages.success(request, "Patient info added successfully.")
        return redirect("doctors:manage_patient")
    return render(request, "doctors/patient_form.html", {"form": form, "mode": "add"})


@doctor_required
def manage_patient(request):
    records = PatientRecord.objects.filter(doctor=request.user.doctor_profile)
    return render(request, "doctors/manage_patient.html", {"records": records})


@doctor_required
def edit_patient(request, pk):
    record = get_object_or_404(PatientRecord, pk=pk)
    form = PatientRecordForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Patient info updated successfully.")
        return redirect("doctors:manage_patient")
    return render(request, "doctors/patient_form.html", {"form": form, "mode": "edit", "record": record})


@doctor_required
def view_patient(request, pk):
    record = get_object_or_404(PatientRecord, pk=pk)
    if request.method == "POST":
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.patient = record
            entry.save()
            messages.success(request, "Medical history has been added.")
            return redirect("doctors:view_patient", pk=record.pk)
        messages.error(request, "Something went wrong. Please check the form and try again.")
    else:
        form = MedicalHistoryForm()
    return render(request, "doctors/view_patient.html", {"record": record, "history": record.history.all(), "form": form})


@doctor_required
def search(request):
    term = request.POST.get("searchdata", "").strip() if request.method == "POST" else ""
    results = None
    if term:
        results = PatientRecord.objects.filter(Q(name__icontains=term) | Q(contact_no__icontains=term))
    return render(request, "doctors/search.html", {"term": term, "results": results})


@doctor_required
@require_GET
def check_patient_email(request):
    email = request.GET.get("email", "").strip()
    taken = bool(email) and PatientRecord.objects.filter(email__iexact=email).exists()
    return JsonResponse({"available": not taken})


@doctor_required
def edit_profile(request):
    doctor = request.user.doctor_profile
    form = DoctorProfileForm(request.POST or None, doctor=doctor, email_editable=False)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor details updated successfully.")
        return redirect("doctors:edit_profile")
    return render(request, "doctors/edit_profile.html", {"form": form})


@doctor_required
def change_password_view(request):
    return change_password(request, "doctors/change_password.html", "doctors:dashboard")
