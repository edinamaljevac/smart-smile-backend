from rest_framework import serializers
from .models import Rating
from appointments.models import Appointment

class RatingSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.user.username", read_only=True)
    patient_name = serializers.CharField(source="patient.user.username", read_only=True)
    appointment_slot = serializers.CharField(source="appointment.slot", read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "appointment",
            "doctor",
            "doctor_name",
            "patient",
            "patient_name",
            "score",
            "comment",
            "appointment_slot",
            "created_at",
        ]
        read_only_fields = ["id", "doctor", "patient", "doctor_name", "patient_name", "created_at"]

    def validate(self, data):

        appointment = data.get('appointment')

        if appointment.status != "completed":
            raise serializers.ValidationError("Možete oceniti samo završene preglede.")

        if hasattr(appointment, 'rating'):
            raise serializers.ValidationError("Ovaj pregled je već ocenjen.")

        return data