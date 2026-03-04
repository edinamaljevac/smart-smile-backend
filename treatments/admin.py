from django.contrib import admin
from .models import Treatment

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_name', 'price', 'created_at')
    search_fields = ('service_name',)
    list_filter = ('created_at',)
