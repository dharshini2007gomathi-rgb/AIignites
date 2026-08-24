from django.contrib import admin
from opportunities.models import Industry, Faculty, Opportunity, OpportunitySkill


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'type', 'location', 'verified_status']
    list_filter = ['type', 'verified_status']


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'college', 'department', 'email']


class OpportunitySkillInline(admin.TabularInline):
    model = OpportunitySkill
    extra = 1


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'location', 'is_active', 'posted_date']
    list_filter = ['type', 'is_active']
    inlines = [OpportunitySkillInline]
