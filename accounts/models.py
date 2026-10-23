from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils import timezone


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # `createsuperuser` produces a hospital administrator.
        extra_fields.setdefault("role", "admin")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    One account table for the three kinds of people who log in. This replaces
    the PHP `users`, `doctors` (login part) and `admin` tables.
    """

    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Administrator"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    # unique, but optional (the PHP admin account had no e-mail)
    email = models.EmailField("email address", unique=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower() or None
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.full_name or self.get_full_name() or self.username

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_hospital_admin(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return self.display_name


class LoginLog(models.Model):
    """Session log. Replaces the PHP `userlog` and `doctorslog` tables."""

    user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="login_logs")
    role = models.CharField(max_length=10, choices=User.Role.choices, db_index=True)
    username = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=True, help_text="True = successful login")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return "%s (%s) %s" % (self.username, self.role, "ok" if self.status else "failed")
