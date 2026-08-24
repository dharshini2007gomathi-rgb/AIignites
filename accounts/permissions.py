"""
Role-based access control decorators and DRF permissions.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def role_required(*roles):
    """View decorator restricting access to specific user roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in roles:
                if request.user.is_superuser and 'ADMIN' in roles:
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied('You do not have permission to access this page.')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_student


class IsIndustry(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_industry


class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_faculty


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_admin


class IsIndustryOrFaculty(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return profile and (profile.is_industry or profile.is_faculty)


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission for student-owned resources."""
    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, 'profile', None)
        if profile and profile.is_admin:
            return True
        if hasattr(obj, 'student'):
            return obj.student.user == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
