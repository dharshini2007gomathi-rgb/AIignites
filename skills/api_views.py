"""REST API views for skills and assessments."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsStudent
from skills.models import Skill, Assessment, CareerPath, ConceptValidationAttempt, ConceptValidationAnswer, ValidationQuestion
from skills.serializers import (
    SkillSerializer, AssessmentSerializer, AssessmentSubmitSerializer,
    CareerPathListSerializer, CareerPathDetailSerializer,
    CareerGapAnalysisResponseSerializer,
    ValidationQuestionStudentSerializer, ConceptTestSubmitSerializer,
    ConceptValidationAttemptListSerializer,
)
from skills.scoring import process_assessment_submission, get_category_profile
from skills.services import (
    get_skill_gap_analysis, calculate_match_score, get_recommended_opportunities,
    get_career_skill_gap_analysis,
)
from skills.concept_test_engine import (
    generate_validation_test, evaluate_validation_attempt, get_attempt_result_summary,
)


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


class StudentCareerGapAnalysisView(APIView):
    """
    Career-Path-Specific Skill Gap Analysis API.
    Supports:
    - GET /api/students/me/career-gap/ (authenticated student only)
    - GET /api/students/<student_id>/career-gap/ (owner student, faculty, admin only)
    - GET /api/skills/career-gap/<student_id>/ (owner student, faculty, admin only)

    Authorization Rules:
    - Normal students can ONLY access their own career gap analysis.
    - Faculty and Admin users can access student data based on platform role architecture.
    - Other roles (e.g. Industry) and unauthorized users are forbidden (HTTP 403 / 401).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        from students.models import Student
        profile = getattr(request.user, 'profile', None)

        if not student_id or student_id == 'me':
            if not hasattr(request.user, 'student'):
                return Response(
                    {'error': 'Only authenticated students can access their personal career gap analysis.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            student = request.user.student
        else:
            student = get_object_or_404(Student, student_id=student_id)

            # Strict authorization check
            is_admin = bool(profile and profile.is_admin)
            is_faculty = bool(profile and profile.is_faculty)
            is_owner = bool(hasattr(request.user, 'student') and request.user.student.student_id == student.student_id)

            if not (is_owner or is_admin or is_faculty):
                return Response(
                    {'error': "You do not have permission to access another student's career gap analysis."},
                    status=status.HTTP_403_FORBIDDEN
                )

        data = get_career_skill_gap_analysis(student)
        serializer = CareerGapAnalysisResponseSerializer(data)
        return Response(serializer.data)


class ConceptTestStartView(APIView):
    """
    Start a new Career-Path-Specific Concept Validation Test attempt.
    Generates a personalized question set based on student's CareerPathSkillRequirements.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        student = request.user.student
        if not student.career_path:
            return Response(
                {'error': 'Please select your target Career Path in your profile before starting the Concept Validation Test.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            attempt, questions = generate_validation_test(student)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ValidationQuestionStudentSerializer(questions, many=True)
        return Response({
            'attempt_id': attempt.id,
            'attempt_number': attempt.attempt_number,
            'career_path': {
                'id': student.career_path.id,
                'name': student.career_path.name,
                'category': student.career_path.career_category,
            },
            'started_at': attempt.started_at.isoformat(),
            'questions_count': len(questions),
            'questions': serializer.data,
            'message': f'Concept validation test started for {student.career_path.name}. Answer all questions and submit.',
        }, status=status.HTTP_201_CREATED)


class ConceptTestSubmitView(APIView):
    """
    Submit answers for a Concept Validation Test attempt.
    Evaluates responses deterministically, updates skill scores, and calculates verified profile.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, attempt_id):
        student = request.user.student
        attempt = get_object_or_404(ConceptValidationAttempt, id=attempt_id)

        if attempt.student != student:
            return Response(
                {'error': 'You do not have permission to submit answers for another student.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ConceptTestSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = evaluate_validation_attempt(attempt, serializer.validated_data['responses'])
        return Response({
            'message': 'Concept validation test submitted and evaluated successfully.',
            'result': result,
        })


class ConceptTestResultView(APIView):
    """
    Retrieve results of a completed Concept Validation Test attempt.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(ConceptValidationAttempt, id=attempt_id)
        profile = getattr(request.user, 'profile', None)
        is_admin = bool(profile and profile.is_admin)
        is_faculty = bool(profile and profile.is_faculty)
        is_owner = bool(hasattr(request.user, 'student') and request.user.student == attempt.student)

        if not (is_owner or is_admin or is_faculty):
            return Response(
                {'error': 'You do not have permission to view detailed answers for this attempt.'},
                status=status.HTTP_403_FORBIDDEN
            )

        result = get_attempt_result_summary(attempt)
        return Response(result)


class ConceptTestHistoryView(APIView):
    """
    Retrieve list of all Concept Validation Test attempts for authenticated student.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user.student
        attempts = ConceptValidationAttempt.objects.filter(student=student).order_by('-started_at')
        serializer = ConceptValidationAttemptListSerializer(attempts, many=True)
        return Response({
            'total_attempts': attempts.count(),
            'validation_status': student.validation_status,
            'is_validated': student.is_skill_validated,
            'attempts': serializer.data,
        })


class ConceptTestStatusView(APIView):
    """
    Get student's validation status and 3-way skill breakdown (Self, Validated, Verified).
    Industry providers can view validation status and scores without seeing raw answer attempts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        from students.models import Student
        profile = getattr(request.user, 'profile', None)

        if not student_id or student_id == 'me':
            if not hasattr(request.user, 'student'):
                return Response({'error': 'Student profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            student = request.user.student
        else:
            student = get_object_or_404(Student, student_id=student_id)

        # Build skill score comparison list
        skills_breakdown = []
        for ss in student.skills.select_related('skill').all():
            skills_breakdown.append({
                'skill_id': ss.skill.skill_id,
                'skill_name': ss.skill.skill_name,
                'category': ss.skill.category,
                'self_assessment_score': float(ss.self_assessment_score) if ss.self_assessment_score is not None else float(ss.score),
                'validated_score': float(ss.validated_score) if ss.validated_score is not None else None,
                'verified_score': float(ss.score),
                'is_validated': ss.is_validated,
            })

        latest_attempt = student.latest_validation_attempt
        latest_info = None
        if latest_attempt:
            latest_info = {
                'attempt_number': latest_attempt.attempt_number,
                'career_path_name': latest_attempt.career_path.name,
                'percentage': float(latest_attempt.percentage),
                'submitted_at': latest_attempt.submitted_at.isoformat() if latest_attempt.submitted_at else None,
            }

        return Response({
            'student_id': student.student_id,
            'name': student.name,
            'is_validated': student.is_skill_validated,
            'validation_status': student.validation_status,
            'career_path': student.career_path.name if student.career_path else None,
            'latest_attempt': latest_info,
            'skills_breakdown': skills_breakdown,
        })




