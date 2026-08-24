"""REST API views for opportunities."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsIndustryOrFaculty, IsStudent
from opportunities.models import Opportunity
from opportunities.serializers import OpportunitySerializer, OpportunityCreateSerializer
from skills.services import get_recommended_opportunities, calculate_match_score
from students.models import Student


class OpportunityListView(generics.ListCreateAPIView):
    queryset = Opportunity.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'location']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OpportunityCreateSerializer
        return OpportunitySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsIndustryOrFaculty()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        profile = user.profile
        if profile.is_industry:
            serializer.save(industry=user.industry)
        elif profile.is_faculty:
            serializer.save(faculty=user.faculty)


class OpportunityDetailView(generics.RetrieveAPIView):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'opportunity_id'


class RecommendedOpportunitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = Student.objects.get(student_id=student_id)
        recommendations = get_recommended_opportunities(student)
        data = []
        for rec in recommendations:
            opp_data = OpportunitySerializer(rec['opportunity']).data
            opp_data['match_score'] = rec['match_score']
            opp_data['skill_gaps'] = rec['skill_gaps']
            data.append(opp_data)
        return Response(data)


class MatchScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id, opportunity_id):
        student = Student.objects.get(student_id=student_id)
        opportunity = Opportunity.objects.get(opportunity_id=opportunity_id)
        result = calculate_match_score(student, opportunity)
        return Response(result)
