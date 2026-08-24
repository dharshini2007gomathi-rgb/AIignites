from django.contrib import admin
from students.models import Student, Certification, Project, Achievement


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'email', 'college', 'course', 'year']
    list_filter = ['course', 'year']
    search_fields = ['name', 'email', 'college']


admin.site.register(Certification)
admin.site.register(Project)
admin.site.register(Achievement)
