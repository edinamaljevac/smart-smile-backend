from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'treatment', 'slot', 'status', 'created_at')
    list_filter = ('doctor', 'status', 'slot__date')
    search_fields = ('patient__user__username', 'doctor__user__username', 'treatment__name')
    ordering = ('slot__date', 'slot__start_time')
