from django.urls import path
from .views import AppointmentListCreateAPIView, AppointmentDetailAPIView, PatientToothRecordListAPIView, ToothRecordCreateAPIView, DentistCreateAppointmentAPIView

urlpatterns = [
    path('', AppointmentListCreateAPIView.as_view(), name='appointments-list-create'),
    path('<int:pk>/', AppointmentDetailAPIView.as_view(), name='appointments-detail'),
    path('patients/<int:patient_id>/tooth-records/', PatientToothRecordListAPIView.as_view(), name="patient-tooth-records"),
    path('tooth-records/', ToothRecordCreateAPIView.as_view(), name="tooth-record-create"),
    path("dentist-create/", DentistCreateAppointmentAPIView.as_view(), name="dentist-create-appointment"),

]
