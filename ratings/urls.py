from django.urls import path
from .views import RatingCreateAPIView, RatingListAPIView, AdminRatingListAPIView, AdminRatingDeleteAPIView

urlpatterns = [
    path('', RatingListAPIView.as_view(), name='ratings-list'),
    path('create/', RatingCreateAPIView.as_view(), name='ratings-create'),
    
    path("admin/", AdminRatingListAPIView.as_view(), name="admin-ratings"),
    path("admin/<int:pk>/", AdminRatingDeleteAPIView.as_view(), name="admin-rating-delete"),
]
