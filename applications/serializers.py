"""Application serializers."""
from rest_framework import serializers
from applications.models import Application, Internship, InternshipProgress


class ApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    company = serializers.CharField(source='opportunity.posted_by', read_only=True)

    class Meta:
        model = Application
        fields = [
            'application_id', 'student', 'student_name', 'opportunity',
            'opportunity_title', 'company', 'resume', 'cover_letter',
            'status', 'applied_date', 'updated_at',
        ]
        read_only_fields = ['application_id', 'status', 'applied_date', 'updated_at']


class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']


class InternshipSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='application.student.name', read_only=True)
    opportunity_title = serializers.CharField(source='application.opportunity.title', read_only=True)

    class Meta:
        model = Internship
        fields = '__all__'


class InternshipProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipProgress
        fields = '__all__'
