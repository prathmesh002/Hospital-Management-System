from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.PatientLoginView.as_view(), name="patient_login"),
    path("doctor/login/", views.DoctorLoginView.as_view(), name="doctor_login"),
    path("admin/login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("register/", views.register_view, name="register"),
    path("check-email/", views.check_email, name="check_email"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
