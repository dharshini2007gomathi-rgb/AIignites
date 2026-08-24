from django.contrib import admin
from accounts.models import UserProfile, EmailVerificationToken


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'email_verified', 'created_at']
    list_filter = ['role', 'email_verified']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'created_at']
