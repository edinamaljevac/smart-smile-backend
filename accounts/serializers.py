from rest_framework import serializers
from .models import User, PatientProfile, DentistProfile
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'phone', 'is_active']

 
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": _("Email je obavezan."),
            "blank": _("Email ne sme biti prazan."),
            "invalid": _("Unesite ispravnu email adresu."),
        }
    )

    username = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": _("Korisničko ime je obavezno."),
            "blank": _("Korisničko ime ne sme biti prazno."),
        }
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        validators=[validate_password],
        error_messages={
            "required": _("Lozinka je obavezna."),
            "blank": _("Lozinka ne sme biti prazna."),
        }
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'role', 'phone']


    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', User.Roles.PATIENT),
            phone=validated_data.get('phone'),
            is_active=False
        )
        return user
    
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Roles.PATIENT),
        write_only=True,
        source='user',
        required=False
    )

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'user_id', 'date_of_birth', 'gender',
            'address', 'emergency_contact_name', 'emergency_contact_phone',
            'medical_notes'
        ]
        read_only_fields = ['id', 'user']

    def validate_user(self, value):
        if value.role != User.Roles.PATIENT:
            raise serializers.ValidationError("Selected user must have PATIENT role.")
        return value


class DentistProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Roles.DENTIST),
        write_only=True,
        source='user',
        required=False
    )

    class Meta:
        model = DentistProfile
        fields = [
            'id', 'user', 'user_id', 'specialization',
            'experience_years', 'biography', 'phone_clinic', 'clinic_address'
        ]
        read_only_fields = ['id', 'user']

    def validate_user(self, value):
        if value.role != User.Roles.DENTIST:
            raise serializers.ValidationError("Selected user must have DENTIST role.")
        return value
