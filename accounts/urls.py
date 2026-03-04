from django.urls import path
from .views import (
    register,
    login,
    users_list,
    patient_list_create,
    patient_profile_detail,
    dentist_list_create,
    dentist_profile_detail,
    my_patient_profile,
    my_dentist_profile,
    toggle_user_active,
    verify_email,
    forgot_password,
    reset_password
)

app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"), 
    path("users/", users_list, name="users-list"),
    path("users/<int:pk>/toggle-active/", toggle_user_active, name="toggle-user-active"),
    path("patients/", patient_list_create, name="patient-list-create"),
    path("patient/<int:pk>/", patient_profile_detail, name="patient-detail"),
    path("dentists/", dentist_list_create, name="dentist-list-create"),
    path("dentist/<int:pk>/", dentist_profile_detail, name="dentist-detail"),
    path("me/patient-profile/", my_patient_profile, name="my-patient-profile"),
    path("me/dentist-profile/", my_dentist_profile, name="my-dentist-profile"),
    path("verify-email/<str:uidb64>/<str:token>/", verify_email, name="verify-email"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("reset-password/<str:uidb64>/<str:token>/", reset_password, name="reset-password"),
]
