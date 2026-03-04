from rest_framework import serializers
from .models import Treatment

class TreatmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source="doctor.user.username",
        read_only=True
    )

    class Meta:
        model = Treatment
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "service_name",
            "description",
            "price",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "doctor",
            "doctor_name",
        ]
