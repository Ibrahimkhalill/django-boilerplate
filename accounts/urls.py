from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import (
    RegisterUserView,
    LoginView,
    UserProfileView,
    OTPViewSet,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetView,
    ChangePasswordView,
)

# Router for OTPViewSet
router = DefaultRouter()
router.register(r'otp', OTPViewSet, basename='otp')

urlpatterns = [
    # Auth
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Password reset/change
    path('password/reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),

    # Include OTP routes from ViewSet
    path('', include(router.urls)),
]
