
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import *
from .helper import create_and_send_otp

from .serializers import *
from src.utils import error_response

User = get_user_model()

import uuid


# ---------------------------
# User Registration

class RegisterUserView(generics.GenericAPIView):
    serializer_class = PreRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pre_reg = serializer.save()
            return Response({
                "message": "OTP sent successfully. Verify to complete registration.",
                "user_id": pre_reg.id
            }, status=status.HTTP_201_CREATED)
        return error_response(code=400, details=serializer.errors)

# ---------------------------
# User Login
# ---------------------------
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        if not serializer.is_valid():
            return error_response(code=400, details=serializer.errors)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        # Ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
            "name": user.email_address.split('@')[0]
        })

        profile_serializer = UserProfileSerializer(profile)
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "email_address": user.email_address,
            "role": user.role,
            "is_verified": user.is_verified,
            "profile": profile_serializer.data,
            "access_token_valid_till": int(refresh.access_token.lifetime.total_seconds()*1000),
        })


# ---------------------------
# User Profile
# ---------------------------

class UserProfileRetrieveView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        print("self.request",self.request.data)
        return get_object_or_404(UserProfile, user=self.request.user)

      


# ---------------------------
# OTP Handling
# ---------------------------
class OTPCreateAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        if not user_id and not email:
            return error_response(
                code=400,
                details={"user_id": ["Required if email not provided"], "email": ["Required if user_id not provided"]}
            )
        purpose = ''
        # Get email from user_id if provided
        if user_id:
            user = PreRegistration.objects.filter(id=user_id).first()
            purpose = 'signup'
            if user is None:
                user = get_object_or_404(User, id=user_id)
                purpose = 'forgot_password'  
            email = user.email_address
        # Delete previous OTPs for this email & purpose
        OTP.objects.filter(email=email, purpose=purpose).delete()

        try:
            create_and_send_otp(email=email, purpose=purpose)
        except Exception as e:
            return error_response(
                code=500,
                message="Failed to send OTP email",
                details={"error": [str(e)]}
            )

        return Response({"message": f"OTP sent to {email} for {purpose}"}, status=status.HTTP_201_CREATED)



class OTPVerifyAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CustomUserCreateSerializer  # use your existing serializer

    def post(self, request):
        user_id = request.data.get('user_id')
        otp_value = request.data.get('verification_code')

        if not user_id or not otp_value:
            return error_response(code=400, details={
                "user_id": ["User id is Required"],
                "verification_code": ["Verification code Required"]
            })

        pre_reg = PreRegistration.objects.filter(id=user_id).first()
        if pre_reg is None:
            return error_response(code=400, details={"user_id": ["Invalid user id or already verified"]})

        otp_obj = get_object_or_404(OTP, email=pre_reg.email_address, purpose='signup')

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
        
        
        otp_obj.attempts = 0
        otp_obj.save()
        
        # OTP valid → create user
        data = {
            "email_address": pre_reg.email_address,
            "password": pre_reg.password,
            "name": pre_reg.name,
            "role": pre_reg.role
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_verified = True
        user.is_active = True
        user.save()
        # Delete pre-registration record
        pre_reg.delete()

        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if pre_reg.name:
            profile.name = pre_reg.name
            profile.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Account verified & created successfully!",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user_id": user.id,
            "email_address": user.email_address,
            "role": user.role,
            "is_verified": user.is_verified,
            "profile": UserProfileSerializer(profile).data,
            "access_token_valid_till": int(refresh.access_token.lifetime.total_seconds()*1000),
        }, status=200)


# ---------------------------
# Password Reset
# ---------------------------
class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email_address')
        if not email:
            return error_response(code=400, details={"email": ["This field is required"]})

        user = get_object_or_404(User, email_address=email)
        if not user.is_verified:
            return error_response(code=400, details={"email": ["This is not a valid user"]})

        # Delete old OTPs
        OTP.objects.filter(email=email, purpose='forgot_password').delete()
        try:
         otp_obj=create_and_send_otp(email=email, purpose='forgot_password')
        except Exception as e:
            return error_response(code=500, message="Failed to send OTP email", details={"error": [str(e)]})

        return Response({"message": "OTP sent to your email", "user_id": user.id, "expires_at": otp_obj.expires_at.timestamp()})


class PasswordResetVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp_value = request.data.get('verification_code')

        if not user_id or not otp_value:
            return error_response(code=400, details={"user_id": ["Required"], "otp": ["Required"]})

        user = get_object_or_404(User, id=user_id)
        otp_obj = get_object_or_404(OTP, email=user.email_address, purpose='forgot_password')

        # Check attempts
        # if otp_obj.attempts >= otp_obj.max_attempts:
        #     return error_response(code=400, details={"otp": ["Maximum attempts exceeded"]})

        # Check OTP
        if otp_obj.code != otp_value:
            otp_obj.increment_attempts()
            return error_response(code=400, details={"otp": ["Invalid OTP"]})

        # Check expiry
        if otp_obj.is_expired():
            return error_response(code=400, details={"otp": ["OTP expired"]})

        # OTP valid — generate secret key
        secret_key = otp_obj.generate_secret_key()
        return Response({"secret_key": secret_key})



class RefreshTokenView(generics.GenericAPIView):
    permission_classes =[AllowAny]
    
    def post(self, request):
        
        refresh_token = request.data.get("refresh_token")
        
        if not refresh_token:
            return Response({"message":"Refresh tojken is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"message":"Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)



class PasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        secret_key = request.data.get('secret_key')
        new_password = request.data.get('new_password')
        
        print("new_password",new_password)

        if not all([user_id, secret_key, new_password]):
            return error_response(code=400, details={"user_id": ["User id is Required"], "secret_key": ["secret_key is Required"], "new_password": ["New Password is Required"]})

        user = get_object_or_404(User, id=user_id)
        otp_obj = get_object_or_404(OTP, email=user.email_address, purpose='forgot_password')

        print("Provided secret_key:", secret_key)
        print("Stored secret_key:", otp_obj.secret_key)
        
        provided_key = request.data.get('secret_key')
        stored_key = otp_obj.secret_key  # UUIDField object

        # Convert string to UUID before comparison
        try:
            provided_uuid = uuid.UUID(provided_key)
        except Exception:
            return error_response(code=400, details={"secret_key": ["Invalid format"]})

        if stored_key != provided_uuid:
            return error_response(code=400, details={"secret_key": ["Invalid secret key"]})
        

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
