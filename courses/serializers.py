"""Course serializers."""
from rest_framework import serializers
from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'course_id', 'course_name', 'skill', 'skill_name', 'level',
            'provider', 'link', 'duration', 'is_free', 'description',
        ]
