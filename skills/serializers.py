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
        fields = [
            'id', 'skill', 'skill_name', 'category', 'score',
            'self_assessment_score', 'validated_score', 'is_validated',
            'assessment_date',
        ]


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


class CareerSkillComparisonSerializer(serializers.Serializer):
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    category = serializers.CharField()
    current_score = serializers.FloatField()
    self_assessment_score = serializers.FloatField(required=False, default=0.0)
    validated_score = serializers.FloatField(required=False, allow_null=True)
    verified_score = serializers.FloatField(required=False, default=0.0)
    is_validated = serializers.BooleanField(required=False, default=False)
    required_score = serializers.FloatField()
    skill_gap = serializers.FloatField()
    gap_percentage = serializers.FloatField()
    achievement_percentage = serializers.FloatField()
    importance_weight = serializers.FloatField()
    priority_level = serializers.CharField()
    skill_status = serializers.CharField()
    priority_score = serializers.FloatField()


class CareerGapAnalysisResponseSerializer(serializers.Serializer):
    has_career_path = serializers.BooleanField()
    career_path = serializers.DictField(required=False, allow_null=True)
    career_readiness_score = serializers.FloatField()
    readiness_label = serializers.CharField(required=False, allow_null=True)
    is_validated = serializers.BooleanField(required=False, default=False)
    validation_status = serializers.CharField(required=False, default='SELF_REPORTED')
    readiness_source = serializers.CharField(required=False, default='SELF_ASSESSMENT')
    skill_comparisons = CareerSkillComparisonSerializer(many=True)
    prioritized_gaps = CareerSkillComparisonSerializer(many=True)
    strengths = CareerSkillComparisonSerializer(many=True)
    total_requirements = serializers.IntegerField()
    gaps_count = serializers.IntegerField()
    strengths_count = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_null=True)


class ValidationQuestionStudentSerializer(serializers.Serializer):
    """Student-facing question serializer (omits correct_answer and explanation)."""
    question_id = serializers.IntegerField()
    skill_id = serializers.IntegerField(source='skill.skill_id')
    skill_name = serializers.CharField(source='skill.skill_name')
    category = serializers.CharField(source='skill.category')
    question_type = serializers.CharField()
    question_text = serializers.CharField()
    case_context = serializers.CharField(allow_blank=True)
    option_a = serializers.CharField()
    option_b = serializers.CharField()
    option_c = serializers.CharField()
    option_d = serializers.CharField()
    difficulty = serializers.CharField()
    marks = serializers.FloatField()


class ConceptTestSubmitSerializer(serializers.Serializer):
    responses = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of {question_id: int, selected_option: str} objects',
    )


class ConceptValidationAttemptListSerializer(serializers.ModelSerializer):
    career_path_name = serializers.CharField(source='career_path.name', read_only=True)

    class Meta:
        from skills.models import ConceptValidationAttempt
        model = ConceptValidationAttempt
        fields = [
            'id', 'attempt_number', 'career_path', 'career_path_name',
            'started_at', 'submitted_at', 'status',
            'total_score', 'max_score', 'percentage', 'skill_scores', 'is_latest',
        ]



