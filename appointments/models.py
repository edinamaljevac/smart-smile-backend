from django.db import models
from accounts.models import DentistProfile, PatientProfile
from treatments.models import Treatment


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Zakazano'),
        ('completed', 'Završeno'),
        ('canceled', 'Otkazano'),
    ]

    doctor = models.ForeignKey(
        DentistProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    slot = models.ForeignKey(
        'slots.Slot',
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    parent_appointment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="follow_up_appointments"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['slot__date', 'slot__start_time']

    def __str__(self):
        return f"{self.patient.user.username} → {self.doctor.user.username} ({self.slot.date} {self.slot.start_time})"
    
class ToothRecord(models.Model):
    FDI_TEETH = (
    [(i, f"Zub {i}") for i in range(11, 19)] +
    [(i, f"Zub {i}") for i in range(21, 29)] +
    [(i, f"Zub {i}") for i in range(31, 39)] +
    [(i, f"Zub {i}") for i in range(41, 49)]
)

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="tooth_records"
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="tooth_records"
    )

    doctor = models.ForeignKey(
        DentistProfile,
        on_delete=models.CASCADE,
        related_name="tooth_records"
    )

    tooth_number = models.IntegerField(choices=FDI_TEETH)
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient.user.username} - Zub {self.tooth_number}"

