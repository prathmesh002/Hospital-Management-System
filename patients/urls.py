from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("book-appointment/", views.book_appointment, name="book_appointment"),
    path("appointments/", views.appointment_history, name="appointment_history"),
    path("appointments/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),
    path("medical-history/", views.medical_history_list, name="medical_history"),
    path("medical-history/<int:pk>/", views.medical_history_detail, name="medical_history_detail"),
    path("profile/", views.edit_profile, name="edit_profile"),
    path("profile/email/", views.change_email, name="change_email"),
    path("change-password/", views.change_password_view, name="change_password"),
]
