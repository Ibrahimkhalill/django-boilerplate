from datetime import timedelta
from django.utils import timezone
from .models import OTP
import random
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
    msg = EmailMultiAlternatives(
        subject='Your OTP Code',
        body=f'Your OTP is {otp}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)



def create_and_send_otp(email, purpose='signup', expiry_minutes=5):
    """
    Generate an OTP, save it in the OTP table, and return it.
    You can also call your email sending logic here.
    """
    # Delete old OTPs
    OTP.objects.filter(email=email, purpose=purpose).delete()

    # Generate OTP
    otp_code = generate_otp()

    # Save OTP
    otp_obj = OTP.objects.create(
        email=email,
        code=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
    )

    # Send OTP email
    try:
        send_otp_email(email=email, otp=otp_code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to send OTP email: {str(e)}")

    return otp_obj
