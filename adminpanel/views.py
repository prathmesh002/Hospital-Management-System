from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import admin_required
from accounts.models import LoginLog
from accounts.views import change_password
from core.forms import MedicalHistoryForm
from core.models import Appointment, ContactQuery, Doctor, PatientRecord, SitePage, Specialization
from doctors.forms import DoctorProfileForm

from .forms import (AboutPageForm, AddDoctorForm, ContactPageForm, DateRangeForm, QueryRemarkForm,
                    SpecializationForm)

User = get_user_model()


@admin_required
def dashboard(request):
    return render(request, "adminpanel/dashboard.html", {
        "total_users": User.objects.filter(role="patient").count(),
        "total_doctors": Doctor.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "total_patients": PatientRecord.objects.count(),
        "new_queries": ContactQuery.objects.filter(is_read=False).count(),
    })


# ---- specializations -------------------------------------------------------
@admin_required
def specializations(request):
    form = SpecializationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor specialization added successfully.")
        return redirect("adminpanel:specializations")
    return render(request, "adminpanel/specializations.html",
                  {"form": form, "specializations": Specialization.objects.all()})


@admin_required
def edit_specialization(request, pk):
    obj = get_object_or_404(Specialization, pk=pk)
    form = SpecializationForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor specialization updated successfully.")
        return redirect("adminpanel:specializations")
    return render(request, "adminpanel/edit_specialization.html", {"form": form})


@admin_required
@require_POST
def delete_specialization(request, pk):
    obj = get_object_or_404(Specialization, pk=pk)
    try:
        obj.delete()
        messages.success(request, "Specialization deleted.")
    except ProtectedError:
        messages.error(request, "Cannot delete: doctors are still assigned to this specialization.")
    return redirect("adminpanel:specializations")


# ---- doctors ---------------------------------------------------------------
@admin_required
def add_doctor(request):
    form = AddDoctorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor info added successfully.")
        return redirect("adminpanel:manage_doctors")
    return render(request, "adminpanel/add_doctor.html", {"form": form})


@admin_required
def manage_doctors(request):
    return render(request, "adminpanel/manage_doctors.html",
                  {"doctors": Doctor.objects.select_related("user", "specialization")})


@admin_required
def edit_doctor(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related("user"), pk=pk)
    form = DoctorProfileForm(request.POST or None, doctor=doctor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor details updated successfully.")
        return redirect("adminpanel:manage_doctors")
    return render(request, "adminpanel/edit_doctor.html", {"form": form, "doctor": doctor})


@admin_required
@require_POST
def delete_doctor(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor.user.delete()   # cascades to the Doctor profile and its appointments; patient files are kept
    messages.success(request, "Doctor deleted.")
    return redirect("adminpanel:manage_doctors")


@admin_required
@require_GET
def check_doctor_email(request):
    email = request.GET.get("email", "").strip()
    taken = bool(email) and User.objects.filter(email__iexact=email).exists()
    return JsonResponse({"available": not taken})


# ---- users (patient accounts) ---------------------------------------------
@admin_required
def manage_users(request):
    return render(request, "adminpanel/manage_users.html", {"users": User.objects.filter(role="patient")})


@admin_required
@require_POST
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk, role="patient")
    user.delete()
    messages.success(request, "User deleted.")
    return redirect("adminpanel:manage_users")


# ---- patients --------------------------------------------------------------
@admin_required
def manage_patients(request):
    return render(request, "adminpanel/manage_patients.html", {"records": PatientRecord.objects.all()})


@admin_required
def view_patient(request, pk):
    record = get_object_or_404(PatientRecord, pk=pk)
    if request.method == "POST":
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.patient = record
            entry.save()
            messages.success(request, "Medical history has been added.")
            return redirect("adminpanel:view_patient", pk=record.pk)
        messages.error(request, "Something went wrong. Please check the form and try again.")
    else:
        form = MedicalHistoryForm()
    return render(request, "adminpanel/view_patient.html", {"record": record, "history": record.history.all(), "form": form})


@admin_required
def patient_search(request):
    term = request.POST.get("searchdata", "").strip() if request.method == "POST" else ""
    results = None
    if term:
        results = PatientRecord.objects.filter(Q(name__icontains=term) | Q(contact_no__icontains=term))
    return render(request, "adminpanel/patient_search.html", {"term": term, "results": results})


@admin_required
def appointment_history(request):
    appts = Appointment.objects.select_related("doctor__user", "patient")
    return render(request, "adminpanel/appointment_history.html", {"appointments": appts})


# ---- contact queries ---------------------------------------------------------
@admin_required
def unread_queries(request):
    return render(request, "adminpanel/queries.html",
                  {"queries": ContactQuery.objects.filter(is_read=False), "heading": "Unread Query", "read": False})


@admin_required
def read_queries(request):
    return render(request, "adminpanel/queries.html",
                  {"queries": ContactQuery.objects.filter(is_read=True), "heading": "Read Query", "read": True})


@admin_required
def query_details(request, pk):
    query = get_object_or_404(ContactQuery, pk=pk)
    form = QueryRemarkForm(request.POST or None, instance=query)
    if request.method == "POST" and form.is_valid():
        q = form.save(commit=False)
        q.is_read = True
        q.remark_updated_at = timezone.now()
        q.save()
        messages.success(request, "Admin remark updated successfully.")
        return redirect("adminpanel:read_queries")
    return render(request, "adminpanel/query_details.html", {"query": query, "form": form})


# ---- logs --------------------------------------------------------------------
@admin_required
def doctor_logs(request):
    return render(request, "adminpanel/logs.html", {"logs": LoginLog.objects.filter(role="doctor"),
                                                    "heading": "Doctor Session Logs"})


@admin_required
def user_logs(request):
    return render(request, "adminpanel/logs.html", {"logs": LoginLog.objects.filter(role="patient"),
                                                    "heading": "User Session Logs"})


# ---- reports -------------------------------------------------------------------
@admin_required
def between_dates_report(request):
    form = DateRangeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        start, end = form.cleaned_data["from_date"], form.cleaned_data["to_date"]
        records = [r for r in PatientRecord.objects.all()
                   if start <= timezone.localtime(r.created_at).date() <= end]
        return render(request, "adminpanel/report_results.html", {"records": records, "start": start, "end": end})
    return render(request, "adminpanel/between_dates_report.html", {"form": form})


# ---- site pages ------------------------------------------------------------------
@admin_required
def about_us(request):
    page = SitePage.get_page(SitePage.ABOUT)
    form = AboutPageForm(request.POST or None, instance=page)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "About Us has been updated.")
        return redirect("adminpanel:about_us")
    return render(request, "adminpanel/page_form.html", {"form": form, "heading": "Update About Us"})


@admin_required
def contact_us(request):
    page = SitePage.get_page(SitePage.CONTACT)
    form = ContactPageForm(request.POST or None, instance=page)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Contact Us has been updated.")
        return redirect("adminpanel:contact_us")
    return render(request, "adminpanel/page_form.html", {"form": form, "heading": "Update Contact Us"})


@admin_required
def change_password_view(request):
    return change_password(request, "adminpanel/change_password.html", "adminpanel:dashboard")
