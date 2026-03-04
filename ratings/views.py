from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter

from .models import Rating
from .serializers import RatingSerializer
from appointments.models import Appointment
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404


class RatingCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Kreiranje ocene pregleda",
        description=(
            "Pacijent može oceniti završen pregled samo jednom. "
            "Pregled mora imati status 'completed', a pacijent može oceniti "
            "samo sopstveni pregled."
        ),
        request=RatingSerializer,
        responses={
            201: RatingSerializer,
            400: OpenApiExample(
                "Nevalidni podaci",
                value={"detail": "Možete oceniti samo završene preglede."}
            ),
            403: OpenApiExample(
                "Zabranjeno",
                value={"detail": "Samo pacijent može ostaviti ocenu."}
            ),
        },
    )
    def post(self, request):
        user = request.user

        if not hasattr(user, 'patient_profile'):
            return Response(
                {"detail": "Samo pacijent može ostaviti ocenu."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RatingSerializer(data=request.data)

        if serializer.is_valid():
            appointment = serializer.validated_data['appointment']

            if appointment.patient != user.patient_profile:
                return Response(
                    {"detail": "Nije moguće oceniti tuđi pregled."},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer.save(
                patient=user.patient_profile,
                doctor=appointment.doctor
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RatingListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lista ocena",
        description=(
            "Vraća listu svih ocena. "
            "Ako je korisnik pacijent, dobija svoje ocene. "
            "Ako je doktor (dentist), dobija ocene od svojih pacijenata."
        ),
        responses={200: RatingSerializer(many=True)},
    )
    def get(self, request):
        user = request.user

        if hasattr(user, 'dentist_profile'):
            ratings = Rating.objects.filter(doctor=user.dentist_profile)
        elif hasattr(user, 'patient_profile'):
            ratings = Rating.objects.filter(patient=user.patient_profile)
        else:
            return Response(
                {"detail": "Nepoznat korisnik."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)


class AdminRatingListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        ratings = Rating.objects.select_related(
            "doctor__user",
            "patient__user",
            "appointment"
        ).order_by("-created_at")

        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)


class AdminRatingDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        rating = get_object_or_404(Rating, pk=pk)
        rating.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)