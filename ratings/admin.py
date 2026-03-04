from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "score", "patient_name", "dentist_name", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("appointment__patient__user__username", "appointment__dentist__user__username", "comment")

    def patient_name(self, obj):
        return obj.appointment.patient.user.username

    def dentist_name(self, obj):
        return obj.appointment.dentist.user.username
