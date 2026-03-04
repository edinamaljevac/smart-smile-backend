from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count
from django.utils.timezone import now, timedelta
from appointments.models import Appointment
from slots.models import Slot

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


class StatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Pregled statistika sistema",
        description=(
            "Vraća statistiku o terminima, zauzetosti slotova i broju pregleda u poslednjih 7 dana. "
            "Ovo koriste doktori i admin panel za prikaz grafikona."
        ),
        responses={
            200: OpenApiResponse(
                description="Statistika uspešno vraćena",
                examples=[
                    OpenApiExample(
                        "Primer statistike",
                        value={
                            "appointments_count": [
                                {"status": "completed", "total": 5},
                                {"status": "scheduled", "total": 3}
                            ],
                            "treatments_count": [
                                {"treatment__service_name": "Plomba", "total": 4}
                            ],
                            "treatments_count_chart": {
                                "labels": ["Plomba"],
                                "data": [4]
                            },
                            "slots_total": 20,
                            "slots_occupied": 12,
                            "slots_available": 8,
                            "slots_chart": {
                                "labels": ["Slobodni", "Zauzeti"],
                                "data": [8, 12]
                            },
                            "appointments_by_day_chart": {
                                "labels": ["2025-12-01", "2025-12-02"],
                                "data": [2, 3]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        appointments_count = Appointment.objects.values('status').annotate(total=Count('id'))

        treatments_count_qs = Appointment.objects.filter(status='completed') \
            .values('treatment__service_name').annotate(total=Count('id'))

        treatments_count_chart = {
            "labels": [item['treatment__service_name'] or "Nepoznat tretman" for item in treatments_count_qs],
            "data": [item['total'] for item in treatments_count_qs]
        }

        total_slots = Slot.objects.count()
        available_slots = Slot.objects.filter(is_available=True).count()
        occupied_slots = total_slots - available_slots

        slots_chart = {
            "labels": ["Slobodni", "Zauzeti"],
            "data": [available_slots, occupied_slots]
        }

        today = now().date()
        week_ago = today - timedelta(days=6)

        appointments_by_day_qs = Appointment.objects.filter(
            created_at__date__range=[week_ago, today]
        ).values('created_at__date').annotate(total=Count('id')).order_by('created_at__date')

        appointments_by_day_chart = {
            "labels": [item['created_at__date'].strftime('%Y-%m-%d') for item in appointments_by_day_qs],
            "data": [item['total'] for item in appointments_by_day_qs]
        }

        return Response({
            "appointments_count": list(appointments_count),
            "treatments_count": list(treatments_count_qs),
            "treatments_count_chart": treatments_count_chart,
            "slots_total": total_slots,
            "slots_occupied": occupied_slots,
            "slots_available": available_slots,
            "slots_chart": slots_chart,
            "appointments_by_day_chart": appointments_by_day_chart
        })


class DentistStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Statistika rada stomatologa",
        description=(
            "Vraća statistiku samo za ulogovanog stomatologa: "
            "preglede po statusu, zauzetost slotova i broj pregleda "
            "u poslednjih 7 dana."
        ),
        responses={
            200: OpenApiResponse(description="Statistika stomatologa"),
            403: OpenApiResponse(description="Samo stomatolog ima pristup"),
        },
    )
    def get(self, request):
        user = request.user

        if not hasattr(user, "dentist_profile"):
            return Response(
                {"detail": "Samo stomatolog ima pristup ovoj statistici."},
                status=status.HTTP_403_FORBIDDEN,
            )

        dentist = user.dentist_profile

        appointments_count = (
            Appointment.objects
            .filter(doctor=dentist)
            .values("status")
            .annotate(total=Count("id"))
        )

        total_slots = Slot.objects.filter(doctor=dentist).count()
        available_slots = Slot.objects.filter(
            doctor=dentist,
            is_available=True
        ).count()
        occupied_slots = total_slots - available_slots

        slots_chart = {
            "labels": ["Slobodni", "Zauzeti"],
            "data": [available_slots, occupied_slots],
        }

        today = now().date()
        week_ago = today - timedelta(days=6)

        appointments_by_day_qs = (
            Appointment.objects
            .filter(
                doctor=dentist,
                created_at__date__range=[week_ago, today]
            )
            .values("created_at__date")
            .annotate(total=Count("id"))
            .order_by("created_at__date")
        )

        appointments_by_day_chart = {
            "labels": [
                item["created_at__date"].strftime("%Y-%m-%d")
                for item in appointments_by_day_qs
            ],
            "data": [item["total"] for item in appointments_by_day_qs],
        }

        return Response({
            "appointments_count": list(appointments_count),
            "slots_total": total_slots,
            "slots_available": available_slots,
            "slots_occupied": occupied_slots,
            "slots_chart": slots_chart,
            "appointments_by_day_chart": appointments_by_day_chart,
        })
