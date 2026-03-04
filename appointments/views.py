from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404

from .models import Appointment, ToothRecord
from .serializers import AppointmentSerializer, ToothRecordSerializer
from slots.models import Slot

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .emails import (
    send_appointment_created_email,
    send_appointment_canceled_email,
    send_appointment_completed_email,
)



class AppointmentListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Dohvati listu pregleda za prijavljenog korisnika",
        description=(
            "Ako je korisnik **DENTIST**, vraća preglede gde je on doktor.\n"
            "Ako je korisnik **PATIENT**, vraća preglede gde je on pacijent.\n"
        ),
        responses={
            200: AppointmentSerializer(many=True),
            403: OpenApiResponse(description="Nepoznat korisnik ili nedovoljne privilegije."),
        }
    )
    def get(self, request):
        user = request.user

        if hasattr(user, 'dentist_profile'):
            appointments = Appointment.objects.filter(doctor=user.dentist_profile)

        elif hasattr(user, 'patient_profile'):
            appointments = Appointment.objects.filter(patient=user.patient_profile)

        else:
            return Response(
                {"detail": "Nepoznat korisnik."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Kreiraj novi pregled (samo pacijent)",
        description=(
            "Pacijent može kreirati novi pregled. Slot mora biti slobodan. "
            "Sistem automatski postavlja pacijenta i doktora na osnovu slota."
        ),
        request=AppointmentSerializer,
        responses={
            201: AppointmentSerializer,
            400: OpenApiResponse(description="Nevalidni podaci ili slot zauzet."),
            403: OpenApiResponse(description="Samo pacijenti mogu kreirati pregled."),
        },
        examples=[
            OpenApiExample(
                "Primjer JSON zahtjeva",
                value={
                    "treatment": 1,
                    "slot": 5
                }
            )
        ]
    )
    def post(self, request):
        user = request.user

        if not hasattr(user, 'patient_profile'):
            return Response(
                {"detail": "Samo pacijent može zakazati pregled."},
                status=status.HTTP_403_FORBIDDEN
            )

        slot_id = request.data.get('slot')
        slot = get_object_or_404(Slot, id=slot_id)

        if not slot.is_available:
            return Response(
                {"detail": "Odabrani slot je zauzet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AppointmentSerializer(data=request.data)

        if serializer.is_valid():
            appointment = serializer.save(
                patient=user.patient_profile,
                doctor=slot.doctor
            )

            slot.is_available = False
            slot.save()

            try:
                send_appointment_created_email(appointment)
            except Exception as e:
                print("Email error:", e)

            return Response(
                AppointmentSerializer(appointment).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        appointment = get_object_or_404(Appointment, pk=pk)

        if hasattr(user, 'dentist_profile') and appointment.doctor == user.dentist_profile:
            return appointment

        if hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile:
            return appointment

        return None

    @extend_schema(
        summary="Dohvati detalje pregleda",
        responses={
            200: AppointmentSerializer,
            403: OpenApiResponse(description="Nedozvoljen pristup."),
            404: OpenApiResponse(description="Termin ne postoji.")
        }
    )
    def get(self, request, pk):
        appointment = self.get_object(pk, request.user)

        if not appointment:
            return Response(
                {"detail": "Nema pristupa."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)

    @extend_schema(
        summary="Ažuriraj pregled (doktor može menjati status)",
        request=AppointmentSerializer,
        responses={
            200: AppointmentSerializer,
            403: OpenApiResponse(description="Pacijent ne može mijenjati status pregleda."),
        }
    )
    def patch(self, request, pk):
        appointment = self.get_object(pk, request.user)

        if not appointment:
            return Response(
                {"detail": "Nema pristupa."},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(request.user, 'patient_profile'):
            if request.data.get("status") != "canceled":
                return Response(
                    {"detail": "Pacijent može samo otkazati termin."},
                    status=status.HTTP_403_FORBIDDEN
                )


        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)

        if serializer.is_valid():
            updated_appointment = serializer.save()

            if updated_appointment.status == 'canceled':
                updated_appointment.slot.is_available = True
                updated_appointment.slot.save()
                
                try:
                    send_appointment_canceled_email(updated_appointment)
                except Exception as e:
                    print("Email error:", e)

            if updated_appointment.status == 'completed':
                try:
                    send_appointment_completed_email(updated_appointment)
                except Exception as e:
                    print("Email error (completed):", e)

            return Response(AppointmentSerializer(updated_appointment).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Obriši pregled",
        responses={
            204: OpenApiResponse(description="Pregled obrisan."),
            403: OpenApiResponse(description="Nema pristupa."),
        }
    )
    def delete(self, request, pk):
        appointment = self.get_object(pk, request.user)

        if not appointment:
            return Response(
                {"detail": "Nema pristupa."},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment.slot.is_available = True
        appointment.slot.save()

        appointment.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PatientToothRecordListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        if not hasattr(request.user, "dentist_profile"):
            return Response(
                {"detail": "Samo doktor ima pristup kartonu pacijenta."},
                status=status.HTTP_403_FORBIDDEN
            )

        records = ToothRecord.objects.filter(patient_id=patient_id)
        serializer = ToothRecordSerializer(records, many=True)
        return Response(serializer.data)


class ToothRecordCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "dentist_profile"):
            return Response(
                {"detail": "Samo doktor može unositi karton."},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment_id = request.data.get("appointment")

        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=request.user.dentist_profile
        )

        serializer = ToothRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                appointment=appointment,
                patient=appointment.patient,
                doctor=request.user.dentist_profile,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DentistCreateAppointmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "dentist_profile"):
            return Response(
                {"detail": "Samo doktor može zakazati termin pacijentu."},
                status=status.HTTP_403_FORBIDDEN
            )

        patient_id = request.data.get("patient")
        slot_id = request.data.get("slot")
        treatment_id = request.data.get("treatment")
        parent_appointment_id = request.data.get("parent_appointment")

        if not patient_id or not slot_id:
            return Response(
                {"detail": "Nedostaju obavezni podaci."},
                status=status.HTTP_400_BAD_REQUEST
            )

        slot = get_object_or_404(Slot, id=slot_id)

        if not slot.is_available:
            return Response(
                {"detail": "Izabrani termin je već zauzet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = Appointment.objects.create(
            doctor=request.user.dentist_profile,
            patient_id=patient_id,
            slot=slot,
            treatment_id=treatment_id,
            parent_appointment_id=parent_appointment_id,
            status="scheduled",
        )

        slot.is_available = False
        slot.save()

        try:
            send_appointment_created_email(appointment)
        except Exception:
            pass

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )

