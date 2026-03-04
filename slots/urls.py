from django.urls import path
from .views import SlotListCreateAPIView, SlotDetailAPIView

urlpatterns = [
    path('', SlotListCreateAPIView.as_view(), name='slots-list-create'),
    path('<int:pk>/', SlotDetailAPIView.as_view(), name='slots-detail'),
]
