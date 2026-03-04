from rest_framework import serializers
from django.utils import timezone
from .models import Slot

class SlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)

    class Meta:
        model = Slot
        fields = ['id', 'doctor', 'doctor_name', 'date', 'start_time', 'end_time', 'is_available']
        read_only_fields = ['id', 'doctor', 'doctor_name']
    
    def validate(self, data):
        date = data.get("date")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        now = timezone.localtime()
        today = now.date()
        current_time = now.time()

        if start_time >= end_time:
            raise serializers.ValidationError({
                "end_time": "Vreme završetka mora biti posle vremena početka."
            })
        
        if date < today:
            raise serializers.ValidationError({
                "date": "Ne možete zakazati termin u prošlosti."
            })
        
        if date == today and start_time <= current_time:
            raise serializers.ValidationError({
                "start_time": "Vreme termina mora biti u budućnosti."
            })
        
        return data