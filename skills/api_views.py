"""REST API views for skills and assessments."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStudent
from skills.models import Skill, Assessment, CareerPath
from skills.serializers import (
    SkillSerializer, AssessmentSerializer, AssessmentSubmitSerializer,
    CareerPathListSerializer, CareerPathDetailSerializer,
)
from skills.scoring import process_assessment_submission, get_category_profile
from skills.services import get_skill_gap_analysis, calculate_match_score, get_recommended_opportunities


class SkillListView(generics.ListAPIView):
    queryset = Skill.objects.filter(is_active=True)
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['skill_name']


class SkillDetailView(generics.RetrieveAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]


class AssessmentListView(generics.ListAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']


class AssessmentSubmitView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        serializer = AssessmentSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student = request.user.student
        result = process_assessment_submission(student, serializer.validated_data['responses'])
        profile = get_category_profile(student)

        return Response({
            'message': 'Assessment submitted successfully.',
            'result': result,
            'skill_profile': profile,
        })


class GapAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        from students.models import Student
        student = Student.objects.get(student_id=student_id)
        gaps = get_skill_gap_analysis(student)
        profile = get_category_profile(student)
        return Response({'gaps': gaps, 'profile': profile})


class CareerPathListView(generics.ListAPIView):
    """List all active predefined Ayurvedic Career Paths."""
    from skills.models import CareerPath
    queryset = CareerPath.objects.filter(is_active=True).prefetch_related('skill_requirements')
    serializer_class = CareerPathListSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['career_category']
    search_fields = ['name', 'description']


class CareerPathDetailView(generics.RetrieveAPIView):
    """Retrieve full details of a Career Path including required skill benchmarks."""
    from skills.models import CareerPath
    queryset = CareerPath.objects.filter(is_active=True).prefetch_related('skill_requirements__skill')
    serializer_class = CareerPathDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

