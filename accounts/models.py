from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        DENTIST = "DENTIST", "Dentist"
        PATIENT = "PATIENT", "Patient"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} - {self.role}"


class PatientProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True, help_text="Bolesti, alergije, terapije, posebne napomene")

    def __str__(self):
        return f"Patient Profile - {self.user.email}"


class DentistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="dentist_profile")
    specialization = models.CharField(max_length=255)
    experience_years = models.IntegerField(default=0)
    biography = models.TextField(blank=True, null=True)
    phone_clinic = models.CharField(max_length=20, blank=True, null=True)
    clinic_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Dentist Profile - {self.user.email}"
