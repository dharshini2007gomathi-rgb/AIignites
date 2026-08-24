"""Student serializers."""
from rest_framework import serializers
from students.models import Student, Certification, Project, Achievement


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'
        read_only_fields = ['student']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['student']


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'
        read_only_fields = ['student']


class StudentSerializer(serializers.ModelSerializer):
    career_path_name = serializers.CharField(source='career_path.name', read_only=True)
    career_path_slug = serializers.CharField(source='career_path.slug', read_only=True)
    career_path_category = serializers.CharField(source='career_path.career_category', read_only=True)

    class Meta:
        model = Student
        fields = [
            'student_id', 'name', 'email', 'college', 'course', 'year',
            'specialization', 'career_goal', 'career_path', 'career_path_name',
            'career_path_slug', 'career_path_category', 'registration_date',
            'bio', 'portfolio_slug', 'created_at', 'updated_at',
        ]
        read_only_fields = ['student_id', 'registration_date', 'created_at', 'updated_at']


class StudentPortfolioSerializer(serializers.ModelSerializer):
    career_path_name = serializers.CharField(source='career_path.name', read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    achievements = AchievementSerializer(many=True, read_only=True)
    skills = serializers.SerializerMethodField()
    internships = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'student_id', 'name', 'email', 'college', 'course', 'year',
            'specialization', 'career_goal', 'career_path', 'career_path_name',
            'bio', 'portfolio_slug', 'certifications', 'projects',
            'achievements', 'skills', 'internships',
        ]

    def get_skills(self, obj):
        return [
            {
                'skill_name': ss.skill.skill_name,
                'category': ss.skill.category,
                'score': float(ss.score),
            }
            for ss in obj.skills.select_related('skill').all()
        ]

    def get_internships(self, obj):
        from applications.models import Internship
        internships = Internship.objects.filter(
            application__student=obj, status='Completed'
        ).select_related('application__opportunity')
        return [
            {
                'title': i.application.opportunity.title,
                'company': i.application.opportunity.posted_by,
                'start_date': i.start_date.isoformat(),
                'end_date': i.end_date.isoformat() if i.end_date else None,
                'certificate_issued': i.certificate_issued,
            }
            for i in internships
        ]
