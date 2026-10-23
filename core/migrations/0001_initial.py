import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("contact_no", models.CharField(max_length=20)),
                ("message", models.TextField()),
                ("posted_at", models.DateTimeField(auto_now_add=True)),
                ("admin_remark", models.TextField(blank=True)),
                ("is_read", models.BooleanField(default=False)),
                ("remark_updated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name_plural": "contact queries",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="SitePage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_type", models.CharField(choices=[("aboutus", "About us"), ("contactus", "Contact us")], max_length=20, unique=True)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("mobile_number", models.CharField(blank=True, max_length=30)),
                ("opening_time", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Specialization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Doctor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("address", models.TextField(verbose_name="Clinic address")),
                ("fees", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Consultancy fees")),
                ("contact_no", models.CharField(max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("specialization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="doctors", to="core.specialization")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="doctor_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="PatientRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("contact_no", models.CharField(max_length=20)),
                ("email", models.EmailField(max_length=254)),
                ("gender", models.CharField(max_length=10)),
                ("address", models.TextField()),
                ("age", models.CharField(max_length=10)),
                ("medical_history", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doctor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="patient_records", to="core.doctor")),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="MedicalHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("blood_pressure", models.CharField(max_length=100)),
                ("blood_sugar", models.CharField(max_length=100)),
                ("weight", models.CharField(max_length=100)),
                ("temperature", models.CharField(max_length=100)),
                ("prescription", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="core.patientrecord")),
            ],
            options={
                "verbose_name_plural": "medical history",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("specialization", models.CharField(max_length=255)),
                ("fees", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Consultancy fees")),
                ("appointment_date", models.DateField()),
                ("appointment_time", models.TimeField()),
                ("user_status", models.BooleanField(default=True, verbose_name="active for patient")),
                ("doctor_status", models.BooleanField(default=True, verbose_name="active for doctor")),
                ("posted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to="core.doctor")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="appointments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
