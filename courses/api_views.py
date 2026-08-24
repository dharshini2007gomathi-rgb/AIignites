"""REST API views for courses."""
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from courses.models import Course
from courses.serializers import CourseSerializer
from skills.services import get_recommended_courses
from students.models import Student


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['skill', 'level', 'is_free']
    search_fields = ['course_name', 'provider']


class RecommendedCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = Student.objects.get(student_id=student_id)
        courses = get_recommended_courses(student)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
