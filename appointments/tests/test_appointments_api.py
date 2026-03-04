import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import date, time, timedelta

from accounts.models import DentistProfile, PatientProfile
from slots.models import Slot
from appointments.models import Appointment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def dentist():
    user = User.objects.create_user(
        username="dentist1",
        email="dentist1@test.com",
        password="test123"
    )
    return DentistProfile.objects.create(user=user)


@pytest.fixture
def patient():
    user = User.objects.create_user(
        username="patient1",
        email="patient1@test.com",
        password="test123"
    )
    return PatientProfile.objects.create(user=user)


@pytest.fixture
def future_slot(dentist):
    return Slot.objects.create(
        doctor=dentist,
        date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        is_available=True
    )


# -------------------------------------------------
# 1️⃣ Pacijent može zakazati termin
# -------------------------------------------------

@pytest.mark.django_db
def test_patient_can_create_appointment(api_client, patient, future_slot):

    api_client.force_authenticate(user=patient.user)

    url = reverse("appointments-list-create")

    response = api_client.post(url, {
        "slot": future_slot.id
    })

    assert response.status_code == 201
    assert Appointment.objects.count() == 1

    future_slot.refresh_from_db()
    assert future_slot.is_available is False


# -------------------------------------------------
# 2️⃣ Ne može zakazati zauzet slot
# -------------------------------------------------

@pytest.mark.django_db
def test_cannot_book_taken_slot(api_client, patient, future_slot):

    future_slot.is_available = False
    future_slot.save()

    api_client.force_authenticate(user=patient.user)

    url = reverse("appointments-list-create")

    response = api_client.post(url, {
        "slot": future_slot.id
    })

    assert response.status_code == 400
    assert "zauzet" in response.data["detail"].lower()


# -------------------------------------------------
# 3️⃣ Pacijent ne može promijeniti status u completed
# -------------------------------------------------

@pytest.mark.django_db
def test_patient_cannot_complete_appointment(api_client, patient, dentist, future_slot):

    appointment = Appointment.objects.create(
        doctor=dentist,
        patient=patient,
        slot=future_slot,
        status="scheduled"
    )

    api_client.force_authenticate(user=patient.user)

    url = reverse("appointments-detail", args=[appointment.id])

    response = api_client.patch(url, {
        "status": "completed"
    })

    assert response.status_code == 403


# -------------------------------------------------
# 4️⃣ Doktor može završiti termin (completed)
# -------------------------------------------------

@pytest.mark.django_db
def test_dentist_can_complete_appointment(api_client, patient, dentist, future_slot):

    appointment = Appointment.objects.create(
        doctor=dentist,
        patient=patient,
        slot=future_slot,
        status="scheduled"
    )

    api_client.force_authenticate(user=dentist.user)

    url = reverse("appointments-detail", args=[appointment.id])

    response = api_client.patch(url, {
        "status": "completed"
    })

    assert response.status_code == 200

    appointment.refresh_from_db()
    assert appointment.status == "completed"
