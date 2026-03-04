from django.urls import path
from .views import StatsAPIView, DentistStatsAPIView

urlpatterns = [
    path('', StatsAPIView.as_view(), name='stats'),
        path("dentist/", DentistStatsAPIView.as_view(), name="dentist-stats"),
]
