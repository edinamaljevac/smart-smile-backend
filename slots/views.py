from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)

from .models import Slot
from .serializers import SlotSerializer


class SlotListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lista svih slotova (doktor → njegovi slotovi, pacijent → samo slobodni)",
        description=(
            "Doktor vidi samo svoje buduće slotove.\n"
            "Pacijent vidi samo slobodne i buduće slotove."
        ),
        responses={200: SlotSerializer(many=True)},
    )
    def get(self, request):
        user = request.user

        now = timezone.localtime()
        today = now.date()
        current_time = now.time()

        # FILTER: samo budući slotovi
        future_slots_filter = Q(date__gt=today) | Q(
            date=today,
            start_time__gt=current_time
        )

        if hasattr(user, "dentist_profile"):
            slots = Slot.objects.filter(
                doctor=user.dentist_profile
            ).filter(future_slots_filter)
        else:
            slots = Slot.objects.filter(
                is_available=True
            ).filter(future_slots_filter)

        serializer = SlotSerializer(slots, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Kreiranje novog termina (samo doktor)",
        description="Samo doktori mogu kreirati slotove. Termin ne sme biti u prošlosti.",
        request=SlotSerializer,
        responses={
            201: SlotSerializer,
            400: OpenApiResponse(description="Nevalidni podaci ili termin već postoji."),
            403: OpenApiResponse(description="Samo doktori mogu kreirati slotove."),
        },
        examples=[
            OpenApiExample(
                "Primer kreiranja slot-a",
                value={
                    "date": "2026-01-05",
                    "start_time": "10:00",
                    "end_time": "11:00",
                },
            )
        ],
    )
    def post(self, request):
        user = request.user

        if not hasattr(user, "dentist_profile"):
            return Response(
                {"detail": "Samo doktori mogu kreirati slotove."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SlotSerializer(data=request.data)

        if serializer.is_valid():
            try:
                slot = serializer.save(doctor=user.dentist_profile)
                return Response(
                    SlotSerializer(slot).data,
                    status=status.HTTP_201_CREATED,
                )

            except IntegrityError:
                return Response(
                    {
                        "detail": "Termin sa ovim datumom i vremenom već postoji."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SlotDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        slot = get_object_or_404(Slot, pk=pk)

        if hasattr(user, "dentist_profile") and slot.doctor == user.dentist_profile:
            return slot

        if hasattr(user, "patient_profile"):
            return slot

        return None

    @extend_schema(
        summary="Detalji jednog slot-a",
        responses={200: SlotSerializer},
    )
    def get(self, request, pk):
        slot = self.get_object(pk, request.user)

        if slot is None:
            return Response(
                {"detail": "Nema pristupa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SlotSerializer(slot)
        return Response(serializer.data)

    @extend_schema(
        summary="Izmena slot-a (samo doktor)",
        request=SlotSerializer,
        responses={200: SlotSerializer},
    )
    def put(self, request, pk):
        slot = self.get_object(pk, request.user)

        if slot is None:
            return Response(
                {"detail": "Samo doktor može menjati slot."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SlotSerializer(slot, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delimična izmena slot-a (samo doktor)",
        request=SlotSerializer,
        responses={200: SlotSerializer},
    )
    def patch(self, request, pk):
        slot = self.get_object(pk, request.user)

        if slot is None:
            return Response(
                {"detail": "Samo doktor može menjati slot."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SlotSerializer(slot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Brisanje slot-a (samo doktor)",
        responses={204: OpenApiResponse(description="Slot obrisan.")},
    )
    def delete(self, request, pk):
        slot = self.get_object(pk, request.user)

        if slot is None:
            return Response(
                {"detail": "Samo doktor može brisati slot."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not slot.is_available:
            return Response(
                {"detail": "Zauzet termin se ne može obrisati."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
