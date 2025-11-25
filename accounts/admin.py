from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser, UserProfile, OTP

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email_address', 'role', 'is_staff', 'is_verified', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_verified', 'is_superuser')
    search_fields = ('email_address',)
    ordering = ('email_address',)
    filter_horizontal = ('groups', 'user_permissions',)

    fieldsets = (
        (None, {'fields': ('email_address', 'password')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),  # remove date_joined
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email_address', 'password1', 'password2', 'role', 'is_verified', 'is_staff', 'is_superuser')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'name', 'phone_number')
    search_fields = ('user__email_address', 'name', 'phone_number')

    def user_email(self, obj):
        return obj.user.email_address
    user_email.short_description = 'User Email'

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'code', 'purpose', 'is_used', 'attempts', 'max_attempts', 'created_at', 'expires_at')
    search_fields = ('email', 'code')
    list_filter = ('purpose', 'is_used', 'created_at')
