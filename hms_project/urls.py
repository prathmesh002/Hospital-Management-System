from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),          # Django's built-in admin (superusers)
    path("", include("core.urls")),                   # public landing page
    path("hms/", include("accounts.urls")),           # login / register / logout / password reset
    path("hms/doctor/", include("doctors.urls")),     # doctor portal
    path("hms/admin/", include("adminpanel.urls")),   # hospital admin portal
    path("hms/", include("patients.urls")),           # patient portal
]
