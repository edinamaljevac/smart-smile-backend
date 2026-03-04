from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Treatment
from .serializers import TreatmentSerializer
from accounts.models import User

from drf_spectacular.utils import extend_schema


def is_dentist(user):
    return user.is_authenticated and user.role == User.Roles.DENTIST


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@extend_schema(summary="Lista i kreiranje tretmana")
def treatments_list_create(request):
    user = request.user

    if request.method == "GET":
        if hasattr(user, "dentist_profile"):
            treatments = Treatment.objects.filter(
                doctor=user.dentist_profile
            )
        else:
            doctor_id = request.query_params.get("doctor")
            if not doctor_id:
                return Response(
                    {"detail": "Parametar doktora je obavezan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            treatments = Treatment.objects.filter(doctor_id=doctor_id)

        serializer = TreatmentSerializer(treatments, many=True)
        return Response(serializer.data)

    if not is_dentist(user):
        return Response(
            {"detail": "Samo stomatolozi mogu da kreiraju tretmane."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = TreatmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(doctor=user.dentist_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@extend_schema(summary="Detalji tretmana")
def treatment_detail(request, pk):
    treatment = get_object_or_404(Treatment, pk=pk)

    if request.method == "GET":
        serializer = TreatmentSerializer(treatment)
        return Response(serializer.data)

    if not is_dentist(request.user):
        return Response(
            {"detail": "Samo stomatolozi mogu da menjaju tretmane."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "DELETE":
        treatment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = TreatmentSerializer(
        treatment,
        data=request.data,
        partial=(request.method == "PATCH"),
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



