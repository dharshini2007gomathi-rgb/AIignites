"""Opportunity serializers."""
from rest_framework import serializers
from opportunities.models import Industry, Faculty, Opportunity, OpportunitySkill
from skills.serializers import SkillSerializer


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = [
            'industry_id', 'company_name', 'type', 'location',
            'website', 'description', 'verified_status', 'created_at',
        ]
        read_only_fields = ['industry_id', 'verified_status', 'created_at']


class OpportunitySkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)

    class Meta:
        model = OpportunitySkill
        fields = ['id', 'skill', 'skill_name', 'required_score', 'weight']


class OpportunitySerializer(serializers.ModelSerializer):
    required_skills = OpportunitySkillSerializer(many=True, read_only=True)
    posted_by = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    match_score = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Opportunity
        fields = [
            'opportunity_id', 'title', 'type', 'description', 'duration',
            'location', 'state', 'data_status', 'status_label',
            'stipend_salary', 'eligibility', 'is_active',
            'posted_date', 'deadline', 'posted_by', 'required_skills', 'match_score',
        ]


class OpportunityCreateSerializer(serializers.ModelSerializer):
    required_skills = OpportunitySkillSerializer(many=True, required=False)

    class Meta:
        model = Opportunity
        fields = [
            'title', 'type', 'description', 'duration', 'location',
            'state', 'data_status',
            'stipend_salary', 'eligibility', 'deadline', 'required_skills',
        ]


    def create(self, validated_data):
        skills_data = validated_data.pop('required_skills', [])
        opportunity = Opportunity.objects.create(**validated_data)
        for skill_data in skills_data:
            OpportunitySkill.objects.create(opportunity=opportunity, **skill_data)
        return opportunity
