from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
import uuid, random
from django.shortcuts import get_object_or_404
from .models import *


from .serializers import (
    CustomUserCreateSerializer,
    UserProfileSerializer,
    OTPSerializer,
    LoginSerializer
)
from src.utils import error_response

User = get_user_model()


# ---------------------------
# Helper Functions
# ---------------------------
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
    msg = EmailMultiAlternatives(
        subject='Your OTP Code',
        body=f'Your OTP is {otp}',
        from_email='hijabpoint374@gmail.com',
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


# ---------------------------
# User Registration
# ---------------------------
class RegisterUserView(generics.CreateAPIView):
    serializer_class = CustomUserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('role') == 'admin':
            return error_response(
                code=403,
                message="Admin role cannot be assigned during registration",
                details={"role": ["Admin role is restricted"]}
            )

        user = serializer.save()

        # Generate OTP
        otp_code = generate_otp()
        OTP.objects.filter(email=user.email).delete()
        otp_data = {'email': user.email, 'otp': otp_code}
        otp_serializer = OTPSerializer(data=otp_data)
        otp_serializer.is_valid(raise_exception=True)
        otp_serializer.save()

        # Send email
        try:
            send_otp_email(email=user.email, otp=otp_code)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return error_response(
                code=500,
                message="Failed to send OTP email",
                details={"error": [str(e)]}
            )

        return Response({
            "message": "User registered. Please verify your email with the OTP sent",
            "user_id": user.id,
            "email": user.email,
        }, status=status.HTTP_201_CREATED)


# ---------------------------
# User Login
# ---------------------------
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        # Ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
            "name": user.email.split('@')[0]
        })

        profile_serializer = UserProfileSerializer(profile)
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "email_address": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "profile": profile_serializer.data,
            "access_token_valid_till": int(refresh.access_token.lifetime.total_seconds()*1000),
        })


# ---------------------------
# User Profile
# ---------------------------
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"name": self.request.user.email.split('@')[0]}
        )
        return profile


# ---------------------------
# OTP Handling
# ---------------------------
class OTPViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['POST'])
    def create_otp(self, request):
        email = request.data.get('email')
        purpose = request.data.get('purpose', 'signup')  # default to signup
        if not email:
            return error_response(code=400, details={"email": ["This field is required"]})

        # Delete old OTPs for this email and purpose
        OTP.objects.filter(email=email, purpose=purpose).delete()

        # Create new OTP with expiration
        otp_code = generate_otp()
        otp_obj = OTP.objects.create(
            email=email,
            code=otp_code,
            purpose=purpose,
            expires_at=OTP.generate_expiry(minutes=5)  # 5 minutes expiry by default
        )

        try:
            send_otp_email(email=email, otp=otp_code)
        except Exception as e:
            return error_response(code=500, message="Failed to send OTP email", details={"error": [str(e)]})

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def verify_otp(self, request):
        user_id = request.data.get('user_id')
        otp_value = request.data.get('otp')
        if not user_id or not otp_value:
            return error_response(code=400, details={"user_id": ["Required"], "otp": ["Required"]})

        user = get_object_or_404(User, id=user_id)
        otp_obj = get_object_or_404(OTP, email=user.email, is_used=False)

        if otp_obj.is_expired():
            return error_response(code=400, details={"otp": ["OTP expired"]})

        if otp_obj.code != otp_value:
            otp_obj.increment_attempts()
            return error_response(code=400, details={"otp": ["Invalid OTP"]})

        # Mark OTP as used
        otp_obj.mark_used()
        user.is_verified = True
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"name": user.email.split('@')[0]})
        profile_serializer = UserProfileSerializer(profile)

        return Response({
            "message": "Email verified successfully",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "email_address": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "profile": profile_serializer.data
        })

# ---------------------------
# Password Reset
# ---------------------------
class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return error_response(code=400, details={"email": ["This field is required"]})

        user = get_object_or_404(User, email=email)
        if not user.is_verified:
            return error_response(code=400, details={"email": ["This is not a valid user"]})

        # Delete old OTPs
        OTP.objects.filter(email=email, purpose='forgot_password').delete()

        # Generate OTP with expiry
        otp_code = generate_otp()
        otp_obj = OTP.objects.create(
            email=email,
            code=otp_code,
            purpose='forgot_password',
            expires_at=OTP.generate_expiry(minutes=5)  # expires in 5 mins
        )

        try:
            send_otp_email(email=email, otp=otp_code)
        except Exception as e:
            return error_response(code=500, message="Failed to send OTP email", details={"error": [str(e)]})

        return Response({"message": "OTP sent to your email", "user_id": user.id})


class PasswordResetVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp_value = request.data.get('otp')

        if not user_id or not otp_value:
            return error_response(code=400, details={"user_id": ["Required"], "otp": ["Required"]})

        user = get_object_or_404(User, id=user_id)
        otp_obj = get_object_or_404(OTP, email=user.email, purpose='forgot_password')

        # Check attempts
        if otp_obj.attempts >= otp_obj.max_attempts:
            return error_response(code=400, details={"otp": ["Maximum attempts exceeded"]})

        # Check OTP
        if otp_obj.code != otp_value:
            otp_obj.increment_attempts()
            return error_response(code=400, details={"otp": ["Invalid OTP"]})

        # Check expiry
        if otp_obj.is_expired():
            return error_response(code=400, details={"otp": ["OTP expired"]})

        # OTP valid — generate secret key
        secret_key = otp_obj.generate_secret_key()
        return Response({"message": "OTP verified", "secret_key": secret_key, "user_id": user.id})



class PasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        secret_key = request.data.get('secret_key')
        new_password = request.data.get('new_password')

        if not all([user_id, secret_key, new_password]):
            return error_response(code=400, details={"user_id": ["Required"], "secret_key": ["Required"], "new_password": ["Required"]})

        user = get_object_or_404(User, id=user_id)
        otp_obj = get_object_or_404(OTP, email=user.email, purpose='forgot_password')

        if otp_obj.secret_key != secret_key:
            return error_response(code=400, details={"secret_key": ["Invalid secret key"]})

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error_response(code=400, details={"new_password": e.messages})

        user.set_password(new_password)
        user.save()
        otp_obj.delete()

        return Response({"message": "Password reset successful"})


# ---------------------------
# Change Password for Authenticated Users
# ---------------------------
class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return error_response(code=400, details={"current_password": ["Required"], "new_password": ["Required"]})

        user = request.user
        if not user.check_password(current_password):
            return error_response(code=400, details={"current_password": ["Incorrect password"]})

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error_response(code=400, details={"new_password": e.messages})

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
