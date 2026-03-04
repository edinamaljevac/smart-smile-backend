from django.urls import path
from .views import treatments_list_create, treatment_detail

urlpatterns = [
    path('', treatments_list_create, name='treatments_list_create'),
    path('<int:pk>/', treatment_detail, name='treatment_detail')
]
