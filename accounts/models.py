from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, Group, Permission

from django.utils import timezone
import uuid
from datetime import timedelta
from django.conf import settings    


class CustomUserManager(BaseUserManager):
    def _create_user(self, email_address, password, **extra_fields):
        if not email_address:
            raise ValueError("Email field is required")

        email = self.normalize_email(email_address)
        role = extra_fields.get('role', 'user')
        if role == 'admin':
            extra_fields['is_verified'] = True
        else:
            extra_fields.setdefault('is_verified', False)
        user = self.model(email_address=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, email_address, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email_address, password, **extra_fields)

    def create_superuser(self, email_address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email_address, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User'),
       
    )

    email_address = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)        
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Change this
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',  # Change this
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    USERNAME_FIELD = 'email_address'
    REQUIRED_FIELDS = []  # Superuser creation will only require email + password

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email_address} ({self.role})"
    
    
    class Meta:
        verbose_name = "User"          # singular display name
        verbose_name_plural = "Users"  # plural display name



class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    name = models.CharField(max_length=500, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    profile_picture = models.ImageField(upload_to="profile", blank=True, null=True)
    
    def __str__(self):
        return getattr(self.user, 'email_address', 'No User')

    class Meta:
        verbose_name = "User Profile"          # singular display name
        verbose_name_plural = "User Profiles"  # plural display name



class OTP(models.Model):
    PURPOSE_CHOICES = (
        ('signup', 'Signup Verification'),
        ('forgot_password', 'Forgot Password'),
    )

    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    secret_key = models.UUIDField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    is_used = models.BooleanField(default=False)  # mark OTP as used
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['email', 'purpose']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.email} ({self.purpose})"

    def save(self, *args, **kwargs):
        # Set expires_at if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.is_used or timezone.now() > self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save()

    def increment_attempts(self):
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.mark_used()
        else:
            self.save()

    def generate_secret_key(self):
        """Generate secret_key AFTER successful OTP verification."""
        self.secret_key = uuid.uuid4()
        self.save()
        return str(self.secret_key)

