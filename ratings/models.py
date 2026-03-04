from django.db import models
from accounts.models import PatientProfile, DentistProfile
from appointments.models import Appointment

class Rating(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="rating")
    doctor = models.ForeignKey(DentistProfile, on_delete=models.CASCADE, related_name="ratings")
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="ratings")

    score = models.PositiveSmallIntegerField() 
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
