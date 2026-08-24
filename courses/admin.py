from django.contrib import admin
from courses.models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'skill', 'level', 'provider', 'is_free']
    list_filter = ['level', 'is_free']
