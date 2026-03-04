from rest_framework import serializers
from .models import Appointment, ToothRecord


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)
    patient_name = serializers.CharField(source='patient.user.username', read_only=True)
    slot_date = serializers.DateField(source='slot.date', read_only=True)
    slot_start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    slot_end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    has_rating = serializers.SerializerMethodField()
    treatment_name = serializers.CharField(source='treatment.service_name', read_only=True
    )

    def get_has_rating(self, obj):
        return hasattr(obj, "rating")

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name',
            'treatment', 'slot', 'slot_date', 'slot_start_time', 'slot_end_time',
            'status', 'created_at', 'updated_at', 'has_rating', 'treatment_name'
        ]
        read_only_fields = [
            'id', 
            'doctor',          
            'patient',         
            'doctor_name',
            'patient_name',
            'slot_date',
            'slot_start_time',
            'slot_end_time',
            'created_at',
            'updated_at'
        ]


class ToothRecordSerializer(serializers.ModelSerializer):
    treatment_name = serializers.CharField(
        source="treatment.service_name",
        read_only=True
    )

    class Meta:
        model = ToothRecord
        fields = [
            "id",
            "appointment",
            "patient",
            "doctor",
            "tooth_number",
            "treatment",
            "treatment_name",
            "note",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "appointment",
            "patient",
            "doctor",
            "created_at",
        ]
