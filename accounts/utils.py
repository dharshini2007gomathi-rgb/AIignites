"""Authentication utilities - registration, email verification."""
import secrets
import logging
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import UserProfile, EmailVerificationToken

logger = logging.getLogger(__name__)


def generate_verification_token(user):
    """Create and return email verification token."""
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.create(user=user, token=token)
    return token


def send_verification_email(user, token):
    """Send email verification link to user."""
    verify_url = f"{settings.SITE_URL}/verify-email/{token}/"
    try:
        send_mail(
            subject='Verify your Ayurveda Portal account',
            message=f'Hi {user.username},\n\nPlease verify your email: {verify_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Verification email sent to %s', user.email)
    except Exception as e:
        logger.error('Failed to send verification email: %s', e)


def send_application_status_email(application):
    """Notify student of application status change."""
    student = application.student
    try:
        send_mail(
            subject=f'Application Update: {application.opportunity.title}',
            message=(
                f'Dear {student.name},\n\n'
                f'Your application for "{application.opportunity.title}" '
                f'has been updated to: {application.status}.\n\n'
                f'Login to view details: {settings.SITE_URL}/student/applications/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error('Failed to send status email: %s', e)


def create_user_with_role(validated_data):
    """Create User, Profile, and role-specific profile."""
    from students.models import Student
    from opportunities.models import Industry, Faculty

    role = validated_data.pop('role')
    password = validated_data.pop('password')
    validated_data.pop('password_confirm', None)

    user = User.objects.create_user(
        username=validated_data['username'],
        email=validated_data['email'],
        password=password,
    )

    profile = user.profile
    profile.role = role
    profile.save()

    if role == 'STUDENT':
        Student.objects.create(
            user=user,
            name=validated_data.get('name', user.username),
            email=validated_data['email'],
            college=validated_data.get('college', ''),
            course=validated_data.get('course', 'BAMS'),
            year=validated_data.get('year', 1),
        )
    elif role == 'INDUSTRY':
        Industry.objects.create(
            user=user,
            company_name=validated_data.get('company_name', user.username),
            type=validated_data.get('company_type', 'Hospital'),
            location=validated_data.get('location', ''),
        )
    elif role == 'FACULTY':
        Faculty.objects.create(
            user=user,
            name=validated_data.get('name', user.username),
            college=validated_data.get('college', ''),
            department=validated_data.get('department', ''),
            designation=validated_data.get('designation', ''),
            email=validated_data['email'],
        )

    token = generate_verification_token(user)
    send_verification_email(user, token)

    return user
