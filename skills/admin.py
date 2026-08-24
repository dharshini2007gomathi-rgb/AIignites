from django.contrib import admin
from skills.models import (
    Skill, StudentSkill, Assessment, StudentAssessmentResponse,
    CareerPath, CareerPathSkillRequirement,
)


class CareerPathSkillRequirementInline(admin.TabularInline):
    model = CareerPathSkillRequirement
    extra = 3
    autocomplete_fields = ['skill']


@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    list_display = ['name', 'career_category', 'slug', 'is_active', 'created_at']
    list_filter = ['career_category', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CareerPathSkillRequirementInline]


@admin.register(CareerPathSkillRequirement)
class CareerPathSkillRequirementAdmin(admin.ModelAdmin):
    list_display = ['career_path', 'skill', 'required_score', 'importance_weight', 'priority_level']
    list_filter = ['priority_level', 'career_path']
    search_fields = ['career_path__name', 'skill__skill_name']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['skill_name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['skill_name']


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ['student', 'skill', 'score', 'assessment_date']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_id', 'category', 'question_type', 'skill']
    list_filter = ['category', 'question_type']


admin.site.register(StudentAssessmentResponse)

