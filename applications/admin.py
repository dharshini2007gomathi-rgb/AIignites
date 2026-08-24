from django.contrib import admin
from applications.models import Application, Internship, InternshipProgress


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'opportunity', 'status', 'applied_date']
    list_filter = ['status']


class InternshipProgressInline(admin.TabularInline):
    model = InternshipProgress
    extra = 0


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ['internship_id', 'application', 'status', 'start_date']
    inlines = [InternshipProgressInline]
