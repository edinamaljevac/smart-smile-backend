from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DentistProfile

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'phone')}),
    )

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'gender', 'medical_notes')
    search_fields = ('user__email', 'user__username')

@admin.register(DentistProfile)
class DentistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'phone_clinic')
    search_fields = ('user__email', 'user__username', 'specialization')

admin.site.register(User, UserAdmin)
