from django.urls import path
from .views import (RegisterView, LogoutView, UserUpdateView, ChangePasswordView,
                      MyTokenObtainPairView, OTPRequestView,
                     PasswordResetConfirmView, CheckOTPView) 
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    
    path('login/', MyTokenObtainPairView.as_view(), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserUpdateView.as_view(), name='profile'),

    path('OTP-request/', OTPRequestView.as_view(), name='otp-request'),
    path('checkOTP/', CheckOTPView.as_view(), name='check-otp'),

    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'), # In user profile section
]
