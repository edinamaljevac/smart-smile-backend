from django.db import models
from accounts.models import DentistProfile

class Slot(models.Model):
    doctor = models.ForeignKey(
        DentistProfile,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_available = models.BooleanField(default=True)  

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} {self.start_time}-{self.end_time}"
