from django.contrib import admin
from skills.models import (
    Skill, StudentSkill, Assessment, StudentAssessmentResponse,
    CareerPath, CareerPathSkillRequirement,
    ValidationQuestion, ConceptValidationAttempt, ConceptValidationAnswer,
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
    list_display = ['student', 'skill', 'score', 'self_assessment_score', 'validated_score', 'is_validated', 'assessment_date']
    list_filter = ['is_validated', 'skill__category']
    search_fields = ['student__student_id', 'student__name', 'skill__skill_name']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_id', 'category', 'question_type', 'skill']
    list_filter = ['category', 'question_type']


class ConceptValidationAnswerInline(admin.TabularInline):
    model = ConceptValidationAnswer
    extra = 0
    readonly_fields = ['question', 'selected_option', 'is_correct', 'score_obtained']


@admin.register(ValidationQuestion)
class ValidationQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_id', 'skill', 'question_type', 'difficulty', 'correct_answer', 'marks', 'is_active']
    list_filter = ['skill', 'question_type', 'difficulty', 'is_active']
    search_fields = ['question_text', 'explanation', 'case_context']


@admin.register(ConceptValidationAttempt)
class ConceptValidationAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'career_path', 'attempt_number', 'percentage', 'status', 'is_latest', 'started_at', 'submitted_at']
    list_filter = ['status', 'career_path', 'is_latest']
    search_fields = ['student__student_id', 'student__name', 'career_path__name']
    inlines = [ConceptValidationAnswerInline]


admin.site.register(StudentAssessmentResponse)
admin.site.register(ConceptValidationAnswer)


