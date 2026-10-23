from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("appointments/", views.appointment_history, name="appointment_history"),
    path("appointments/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),
    path("patients/add/", views.add_patient, name="add_patient"),
    path("patients/", views.manage_patient, name="manage_patient"),
    path("patients/<int:pk>/edit/", views.edit_patient, name="edit_patient"),
    path("patients/<int:pk>/", views.view_patient, name="view_patient"),
    path("search/", views.search, name="search"),
    path("check-patient-email/", views.check_patient_email, name="check_patient_email"),
    path("profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password_view, name="change_password"),
]
