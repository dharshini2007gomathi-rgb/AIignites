"""
User profile and role management for the Ayurveda Skill Mapping Portal.
Extends Django's built-in User with role-based access control.
"""
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extended profile linking Django User to a platform role."""

    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('INDUSTRY', 'Industry'),
        ('FACULTY', 'Faculty'),
        ('ADMIN', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_industry(self):
        return self.role == 'INDUSTRY'

    @property
    def is_faculty(self):
        return self.role == 'FACULTY'

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser


class EmailVerificationToken(models.Model):
    """Token for email verification on registration."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification token for {self.user.email}"
