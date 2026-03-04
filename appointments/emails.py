from django.core.mail import send_mail
from django.conf import settings


def send_appointment_created_email(appointment):

    patient_email = appointment.patient.user.email
    doctor_email = appointment.doctor.user.email
    start_time = appointment.slot.start_time.strftime("%H:%M")
    end_time = appointment.slot.end_time.strftime("%H:%M")


    patient_subject = "Uspešno ste zakazali termin – SmartSmile"

    patient_message = (
        f"Poštovani {appointment.patient.user.username},\n\n"
        f"Vaš termin je uspešno zakazan.\n\n"
        f"Doktor: Dr. {appointment.doctor.user.username}\n"
        f"Datum: {appointment.slot.date}\n"
        f"Vreme: {start_time} - {end_time}\n\n"
        f"Hvala što koristite SmartSmile."
    )

    send_mail(
        patient_subject,
        patient_message,
        settings.DEFAULT_FROM_EMAIL,
        [patient_email],
        fail_silently=False,
    )

    doctor_subject = "Novi termin je zakazan – SmartSmile"

    doctor_message = (
        f"Poštovani dr. {appointment.doctor.user.username},\n\n"
        f"Zakazan je novi termin.\n\n"
        f"Pacijent: {appointment.patient.user.username}\n"
        f"Datum: {appointment.slot.date}\n"
        f"Vreme: {start_time} - {end_time}\n\n"
        f"SmartSmile sistem"
    )

    send_mail(
        doctor_subject,
        doctor_message,
        settings.DEFAULT_FROM_EMAIL,
        [doctor_email],
        fail_silently=False,
    )


def send_appointment_canceled_email(appointment):
    patient_email = appointment.patient.user.email
    doctor_email = appointment.doctor.user.email
    start_time = appointment.slot.start_time.strftime("%H:%M")
    end_time = appointment.slot.end_time.strftime("%H:%M")

    patient_subject = "Termin je otkazan – SmartSmile"

    patient_message = (
        f"Poštovani {appointment.patient.user.username},\n\n"
        f"Vaš termin je otkazan.\n\n"
        f"Doktor: Dr. {appointment.doctor.user.username}\n"
        f"Datum: {appointment.slot.date}\n"
        f"Vreme: {start_time} - {end_time}\n\n"
        f"Ukoliko želite, možete zakazati novi termin putem SmartSmile sistema."
    )

    send_mail(
        patient_subject,
        patient_message,
        settings.DEFAULT_FROM_EMAIL,
        [patient_email],
        fail_silently=False,
    )

    doctor_subject = "Termin je otkazan – SmartSmile"

    doctor_message = (
        f"Poštovani dr. {appointment.doctor.user.username},\n\n"
        f"Termin je otkazan.\n\n"
        f"Pacijent: {appointment.patient.user.username}\n"
        f"Datum: {appointment.slot.date}\n"
        f"Vreme: {start_time} - {end_time}\n\n"
        f"SmartSmile sistem"
    )

    send_mail(
        doctor_subject,
        doctor_message,
        settings.DEFAULT_FROM_EMAIL,
        [doctor_email],
        fail_silently=False,
    )


def send_appointment_completed_email(appointment):
    patient_email = appointment.patient.user.email
    start_time = appointment.slot.start_time.strftime("%H:%M")
    end_time = appointment.slot.end_time.strftime("%H:%M")

    subject = "Pregled je završen – SmartSmile"

    message = (
        f"Poštovani {appointment.patient.user.username},\n\n"
        f"Vaš pregled je uspešno završen.\n\n"
        f"Doktor: Dr. {appointment.doctor.user.username}\n"
        f"Datum: {appointment.slot.date}\n"
        f"Vreme: {start_time} - {end_time}\n\n"
        f"Možete ostaviti ocenu i komentar za ovaj pregled "
        f"putem SmartSmile sistema.\n\n"
        f"Hvala što koristite SmartSmile."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [patient_email],
        fail_silently=False,
    )
