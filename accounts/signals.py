# signals.py in accounts app
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create a new profile for new users
        UserProfile.objects.create(
            user=instance,
            name=instance.email_address.split('@')[0]  # default name
        )
    else:
        # Update profile if user already exists
        UserProfile.objects.update_or_create(
            user=instance,
            defaults={
                'name': instance.email_address.split('@')[0]
            }
        )
