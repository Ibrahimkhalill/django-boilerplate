from django.urls import path

from accounts.views import (
    RegisterUserView,
    LoginView,
    UserProfileRetrieveView,
    UserProfileUpdateView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetView,
    ChangePasswordView,
    OTPCreateAPIView,
    OTPVerifyAPIView,
    RefreshTokenView 
)
urlpatterns = [
    # Auth
    path('sign-up', RegisterUserView.as_view(), name='register'),
    path('sign-in', LoginView.as_view(), name='login'),

    # User profile
    path('profile', UserProfileRetrieveView.as_view(), name='user-profile-retrieve'),  # GET for profile
    path('profile/update', UserProfileUpdateView.as_view(), name='user-profile-update'),  # PUT/PATCH for updating profile

    # Password reset/change
    path('forgot-password', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('verify-reset-code', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('reset-password', PasswordResetView.as_view(), name='password-reset'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),
    path('resend-verification-code', OTPCreateAPIView.as_view(), name='new-otp-careate'),
    path('verify-email', OTPVerifyAPIView.as_view(), name='otp-verify'),
    path('refresh', RefreshTokenView.as_view(), name='refresh-token'),


]
