"""REST API views for students."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStudent, IsOwnerOrAdmin, IsAdminRole
from students.models import Student
from students.serializers import StudentSerializer, StudentPortfolioSerializer
from skills.serializers import StudentSkillSerializer


class StudentListView(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]


class StudentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'student_id'


class StudentSkillsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = Student.objects.get(student_id=student_id)
        skills = student.skills.select_related('skill').all()
        serializer = StudentSkillSerializer(skills, many=True)
        return Response(serializer.data)


class StudentPortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = Student.objects.get(student_id=student_id)
        serializer = StudentPortfolioSerializer(student)
        return Response(serializer.data)
