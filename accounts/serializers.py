from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import *
from .helper import create_and_send_otp

User = get_user_model()


# ---------------------------
# UserProfile Serializer
# ---------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'name', 'phone_number', 'profile_picture','file']
        read_only_fields = ['id', 'user']

    def validate(self, data):
        errors = {}
        if 'name' in data and not data['name']:
            errors['name'] = ['Name cannot be empty']
        if errors:
            raise serializers.ValidationError(errors)
        return data


# ---------------------------
class PreRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreRegistration
        fields = ['id', 'email_address', 'password', 'name', 'phone_number', 'role', 'is_verified', 'date_joined']
        read_only_fields = ['is_verified', 'date_joined']

    def validate_email_address(self, value):
        if User.objects.filter(email_address=value, is_verified=True).exists():
            raise serializers.ValidationError("This email already exists")
        return value

    def create(self, validated_data):
        email = validated_data['email_address']

        # Save / update PreRegistration
        pre_reg, _ = PreRegistration.objects.update_or_create(
            email_address=email,
            defaults=validated_data
        )

        try:
            create_and_send_otp(email=email, purpose='signup')
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise serializers.ValidationError({"otp": f"Failed to send OTP: {str(e)}"})

        return pre_reg
       


# ---------------------------
# CustomUser Serializer
# ---------------------------
class CustomUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email_address', 'role', 'is_verified', 'profile', 'date_joined', 'updated_at']
        read_only_fields = ['id', 'role', 'is_verified', 'date_joined', 'updated_at', 'is_staff', 'is_superuser']


# ---------------------------
# CustomUser Create Serializer
# ---------------------------
class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLES, default='user')

    class Meta:
        model = User
        fields = ['id', 'email_address', 'password', 'role', 'name', 'phone_number']
        extra_kwargs = {'email_address': {'required': True}, 'password': {'required': True}}

    def validate(self, data):
        errors = {}

        if not data.get('email_address'):
            errors['email_address'] = ['This field is required']
        if not data.get('password'):
            errors['password'] = ['This field is required']
        if not data.get('name'):
            errors['name'] = ['This field is required']

        # Check if verified user already exists
        if User.objects.filter(email_address=data.get('email_address'), is_verified=True).exists():
            errors['email_address'] = ['A verified user with this email already exists']

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
   
        # Check for unverified user
        user = User.objects.filter(email_address=validated_data['email_address'], is_verified=False).first()

        if user:
            # Update existing unverified user
            user.set_password(validated_data['password'])
            user.role = validated_data.get('role', 'user')
            user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                email_address=validated_data['email_address'],
                password=validated_data['password'],
                role=validated_data.get('role', 'user')
            )

        return user


# ---------------------------
# Login Serializer
# ---------------------------
class LoginSerializer(serializers.Serializer):
    email_address = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email_address')
        password = data.get('password')
        errors = {}

        if not email:
            errors['email_address'] = ['This field is required']
        if not password:
            errors['password'] = ['This field is required']

        if errors:
            raise serializers.ValidationError(errors)

        user = authenticate(email_address=email, password=password)
        
        print("Authenticated User:", user)
        if not user:
            raise serializers.ValidationError({'credentials': ['Invalid email or password']})

        if not user.is_active or not user.is_verified:
            raise serializers.ValidationError({'credentials': ['Invalid email or password']})

        return user


# ---------------------------
# OTP Serializer
# ---------------------------
class OTPSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)

    class Meta:
        model = OTP
        fields = ['id', 'email', 'code', 'purpose', 'created_at', 'attempts', 'expires_at']
        read_only_fields = ['id', 'created_at', 'attempts', 'expires_at']

    def validate(self, data):
        errors = {}
        if not data.get('email'):
            errors['email'] = ['This field is required']
        if not data.get('code'):
            errors['code'] = ['This field is required']

        if errors:
            raise serializers.ValidationError(errors)

        return data





