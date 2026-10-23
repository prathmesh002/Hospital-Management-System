from django.contrib import admin

from . import models

admin.site.register(models.Specialization)
admin.site.register(models.Doctor)
admin.site.register(models.PatientRecord)
admin.site.register(models.MedicalHistory)
admin.site.register(models.Appointment)
admin.site.register(models.ContactQuery)
admin.site.register(models.SitePage)
