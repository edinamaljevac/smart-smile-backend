from django.db import models
from accounts.models import DentistProfile

class Treatment(models.Model):
    doctor = models.ForeignKey(
        DentistProfile,
        on_delete=models.CASCADE,
        related_name="treatments"
    )
    service_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} ({self.doctor.user.username})"
