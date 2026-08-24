"""Skill serializers."""
from rest_framework import serializers
from skills.models import Skill, StudentSkill, Assessment, StudentAssessmentResponse


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['skill_id', 'skill_name', 'category', 'description', 'is_active']


class StudentSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = StudentSkill
        fields = ['id', 'skill', 'skill_name', 'category', 'score', 'assessment_date']


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'assessment_id', 'skill', 'question_text', 'question_type',
            'options', 'max_score', 'category',
        ]


class AssessmentSubmitSerializer(serializers.Serializer):
    responses = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of {assessment_id, answer} objects',
    )


class GapAnalysisSerializer(serializers.Serializer):
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    category = serializers.CharField()
    current_score = serializers.FloatField()
    industry_average = serializers.FloatField(required=False)
    required_score = serializers.FloatField(required=False)
    gap = serializers.FloatField()


class CareerPathSkillRequirementSerializer(serializers.ModelSerializer):
    skill_id = serializers.IntegerField(source='skill.skill_id', read_only=True)
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        from skills.models import CareerPathSkillRequirement
        model = CareerPathSkillRequirement
        fields = [
            'id', 'skill_id', 'skill_name', 'category',
            'required_score', 'importance_weight', 'priority_level',
        ]


class CareerPathListSerializer(serializers.ModelSerializer):
    skills_count = serializers.IntegerField(source='skill_requirements.count', read_only=True)

    class Meta:
        from skills.models import CareerPath
        model = CareerPath
        fields = [
            'id', 'name', 'slug', 'career_category',
            'description', 'is_active', 'skills_count',
        ]


class CareerPathDetailSerializer(serializers.ModelSerializer):
    skill_requirements = CareerPathSkillRequirementSerializer(many=True, read_only=True)

    class Meta:
        from skills.models import CareerPath
        model = CareerPath
        fields = [
            'id', 'name', 'slug', 'career_category',
            'description', 'is_active', 'skill_requirements',
            'created_at', 'updated_at',
        ]

