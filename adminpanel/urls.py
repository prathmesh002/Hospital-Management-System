from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("specializations/", views.specializations, name="specializations"),
    path("specializations/<int:pk>/edit/", views.edit_specialization, name="edit_specialization"),
    path("specializations/<int:pk>/delete/", views.delete_specialization, name="delete_specialization"),
    path("doctors/add/", views.add_doctor, name="add_doctor"),
    path("doctors/", views.manage_doctors, name="manage_doctors"),
    path("doctors/<int:pk>/edit/", views.edit_doctor, name="edit_doctor"),
    path("doctors/<int:pk>/delete/", views.delete_doctor, name="delete_doctor"),
    path("check-email/", views.check_doctor_email, name="check_email"),
    path("users/", views.manage_users, name="manage_users"),
    path("users/<int:pk>/delete/", views.delete_user, name="delete_user"),
    path("patients/", views.manage_patients, name="manage_patients"),
    path("patients/<int:pk>/", views.view_patient, name="view_patient"),
    path("patient-search/", views.patient_search, name="patient_search"),
    path("appointments/", views.appointment_history, name="appointment_history"),
    path("queries/unread/", views.unread_queries, name="unread_queries"),
    path("queries/read/", views.read_queries, name="read_queries"),
    path("queries/<int:pk>/", views.query_details, name="query_details"),
    path("logs/doctors/", views.doctor_logs, name="doctor_logs"),
    path("logs/users/", views.user_logs, name="user_logs"),
    path("reports/between-dates/", views.between_dates_report, name="between_dates_report"),
    path("pages/about-us/", views.about_us, name="about_us"),
    path("pages/contact-us/", views.contact_us, name="contact_us"),
    path("change-password/", views.change_password_view, name="change_password"),
]
