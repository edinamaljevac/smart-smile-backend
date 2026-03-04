from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings


from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .models import User, PatientProfile, DentistProfile
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    PatientProfileSerializer,
    DentistProfileSerializer,
    ResetPasswordSerializer
)

def is_dentist(user):
    return user.is_authenticated and user.role == User.Roles.DENTIST

def is_patient(user):
    return user.is_authenticated and user.role == User.Roles.PATIENT


@extend_schema(
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User successfully registered",
            response=RegisterSerializer
        ),
        400: OpenApiResponse(description="Validation error")
    },
    examples=[
        OpenApiExample(
            "Register example",
            value={
                "email": "john@gmail.com",
                "username": "john",
                "password": "Test12345!",
                "role": "PATIENT",
                "phone": "061234567"
            }
        )
    ]
)
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        verify_url = f"https://smart-smile-backend-eiiud.ondigitalocean.app/verify-email/{uid}/{token}/"

        send_mail(
            subject="Potvrdite vaš SmartSmile nalog",
            message=(
                "Hvala na registraciji na SmartSmile platformi.\n\n"
                "Kliknite na link ispod kako biste aktivirali vaš nalog:\n\n"
                f"{verify_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {
                "detail": "Uspešna registracija. Proverite email kako biste aktivirali nalog."
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "example": "john@gmail.com"},
                "password": {"type": "string", "example": "Test12345!"}
            },
            "required": ["email", "password"]
        }
    },
    responses={
        200: OpenApiResponse(description="Login success"),
        400: OpenApiResponse(description="Email/password missing"),
        401: OpenApiResponse(description="Invalid credentials")
    }
)
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"detail": "Email i lozinka su obavezni."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "Neispravan email ili lozinka."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {"detail": "Vaš nalog je deaktiviran od strane administratora."},
            status=status.HTTP_403_FORBIDDEN
    )

    if not check_password(password, user.password):
        return Response(
            {"detail": "Neispravan email ili lozinka."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "phone": user.phone,
        "token": token.key
    }, status=status.HTTP_200_OK)

@extend_schema(
    responses=UserSerializer(many=True)
)
@api_view(['GET'])
def users_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_user_active(request, pk):
    """
    ADMIN: Aktivira / deaktivira korisnika
    """
    if request.user.role != User.Roles.ADMIN:
        return Response(
            {"detail": "Samo administrator može izvršiti ovu akciju."},
            status=status.HTTP_403_FORBIDDEN
        )

    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        return Response(
            {"detail": "Ne možete deaktivirati sopstveni nalog."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.is_active = not user.is_active
    user.save()

    return Response(UserSerializer(user).data)


@extend_schema(
    request=PatientProfileSerializer,
    responses=PatientProfileSerializer(many=True)
)
@api_view(['GET', 'POST'])
def patient_list_create(request):
    if request.method == "GET":
        if not is_dentist(request.user):
            return Response({"detail": "Nemate dozvolu za ovu akciju."}, status=status.HTTP_403_FORBIDDEN)
        patients = PatientProfile.objects.all()
        serializer = PatientProfileSerializer(patients, many=True)
        return Response(serializer.data)
    
    if request.method == "POST":
        if not is_patient(request.user):
            return Response({"detail": "Samo pacijenti mogu kreirati svoj profil."}, status=status.HTTP_403_FORBIDDEN)
        if hasattr(request.user, 'patient_profile'):
            return Response({"detail": "Profil već postoji."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PatientProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=PatientProfileSerializer,
    responses=PatientProfileSerializer
)
@api_view(['GET', 'PUT', 'PATCH'])
def patient_profile_detail(request, pk):
    patient = get_object_or_404(PatientProfile, pk=pk)

    if is_patient(request.user) and patient.user != request.user:
        return Response({"detail": "Nemate dozvolu za ovu akciju."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = PatientProfileSerializer(patient)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        if not (patient.user == request.user):
            return Response({"detail": "Samo vlasnik profila može izmeniti svoj profil."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PatientProfileSerializer(patient, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@extend_schema(
    request=DentistProfileSerializer,
    responses=DentistProfileSerializer(many=True)
)
@api_view(['GET', 'POST'])
def dentist_list_create(request):
    if request.method == "GET":
        dentists = DentistProfile.objects.all()
        serializer = DentistProfileSerializer(dentists, many=True)
        return Response(serializer.data)
    
    if request.method == "POST":
        if not is_dentist(request.user):
            return Response({"detail": "Samo stomatolozi mogu kreirati profil stomatologa."}, status=status.HTTP_403_FORBIDDEN)
        if hasattr(request.user, 'dentist_profile'):
            return Response({"detail": "Profil već postoji."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DentistProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=DentistProfileSerializer,
    responses=DentistProfileSerializer
)
@api_view(['GET', 'PUT', 'PATCH'])
def dentist_profile_detail(request, pk):
    dentist = get_object_or_404(DentistProfile, pk=pk)

    if request.method == 'GET':
        serializer = DentistProfileSerializer(dentist)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        if not (is_dentist(request.user) and dentist.user == request.user):
            return Response({"detail": "Samo stomatolog vlasnik profila može izmeniti svoj profil."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DentistProfileSerializer(dentist, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAuthenticated])
def my_patient_profile(request):
    """
    GET   -> vraca profil ulogovanog pacijenta
    POST  -> kreira profil (ako ne postoji)
    PATCH -> parcijalno azurira profil
    """

    if request.method == "GET":
        try:
            profile = request.user.patient_profile
        except PatientProfile.DoesNotExist:
            return Response(
                {"detail": "Profil ne postoji."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PatientProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        if not is_patient(request.user):
            return Response(
                {"detail": "Samo pacijenti mogu kreirati svoj profil."},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(request.user, "patient_profile"):
            return Response(
                {"detail": "Profil već postoji."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PatientProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == "PATCH":
        try:
            profile = request.user.patient_profile
        except PatientProfile.DoesNotExist:
            return Response(
                {"detail": "Profil ne postoji."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PatientProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAuthenticated])
def my_dentist_profile(request):
    """
    GET   -> vraca profil ulogovanog stomatologa
    POST  -> kreira profil (ako ne postoji)
    PATCH -> parcijalno azurira profil
    """

    if request.method == "GET":
        try:
            profile = request.user.dentist_profile
        except DentistProfile.DoesNotExist:
            return Response(
                {"detail": "Profil ne postoji."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DentistProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        if not is_dentist(request.user):
            return Response(
                {"detail": "Samo stomatolozi mogu kreirati svoj profil."},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(request.user, "dentist_profile"):
            return Response(
                {"detail": "Profil već postoji."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DentistProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == "PATCH":
        try:
            profile = request.user.dentist_profile
        except DentistProfile.DoesNotExist:
            return Response(
                {"detail": "Profile does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DentistProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        return Response(
            {"detail": "Neispravan verifikacioni link."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return Response(
            {"detail": "Email je uspešno potvrđen. Sada se možete prijaviti."},
            status=status.HTTP_200_OK
        )

    return Response(
        {"detail": "Verifikacioni link je istekao ili nije validan."},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
def forgot_password(request):
    email = request.data.get("email")

    if not email:
        return Response(
            {"detail": "Email je obavezan."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "Ako nalog postoji, email za reset lozinke je poslat."},
            status=status.HTTP_200_OK
        )

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_url = f"https://smart-smile-backend-eiiud.ondigitalocean.app/reset-password/{uid}/{token}/"

    send_mail(
        subject="Reset lozinke – SmartSmile",
        message=(
            "Zatražili ste reset lozinke.\n\n"
            "Kliknite na link ispod kako biste postavili novu lozinku:\n\n"
            f"{reset_url}\n\n"
            "Ako niste vi, ignorišite ovaj email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response(
        {"detail": "Ako nalog postoji, email za reset lozinke je poslat."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        return Response(
            {"detail": "Neispravan link."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not default_token_generator.check_token(user, token):
        return Response(
            {"detail": "Link je istekao ili nije validan."},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"detail": serializer.errors["password"]},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(serializer.validated_data["password"])
    user.save()

    return Response(
        {"detail": "Lozinka je uspešno promenjena."},
        status=status.HTTP_200_OK
    )
