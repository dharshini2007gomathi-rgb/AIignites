"""Admin analytics API views."""
from django.db.models import Count, Avg
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole
from students.models import Student
from opportunities.models import Industry, Opportunity, OpportunitySkill
from applications.models import Application
from skills.models import StudentSkill, StudentAssessmentResponse
from skills.services import get_skill_gap_analysis


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        placements = Application.objects.filter(status='Selected').count()
        assessments_done = StudentAssessmentResponse.objects.values('student').distinct().count()

        return Response({
            'total_students': Student.objects.count(),
            'total_industries': Industry.objects.count(),
            'total_opportunities': Opportunity.objects.filter(is_active=True).count(),
            'total_applications': Application.objects.count(),
            'assessments_completed': assessments_done,
            'placements': placements,
        })


class SkillGapsAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        # Aggregate average student scores vs industry requirements
        avg_student_scores = (
            StudentSkill.objects
            .values('skill__skill_name', 'skill__category')
            .annotate(avg_score=Avg('score'))
        )
        avg_requirements = (
            OpportunitySkill.objects
            .values('skill__skill_name', 'skill__category')
            .annotate(avg_required=Avg('required_score'))
        )

        req_map = {
            r['skill__skill_name']: float(r['avg_required'])
            for r in avg_requirements
        }

        gaps = []
        for s in avg_student_scores:
            name = s['skill__skill_name']
            avg = float(s['avg_score'] or 0)
            required = req_map.get(name, 0)
            gap = required - avg
            if gap > 0:
                gaps.append({
                    'skill_name': name,
                    'category': s['skill__category'],
                    'avg_student_score': round(avg, 2),
                    'avg_required': round(required, 2),
                    'gap': round(gap, 2),
                })

        gaps.sort(key=lambda x: x['gap'], reverse=True)
        return Response(gaps[:20])


class IndustryDemandView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        demand = (
            OpportunitySkill.objects
            .filter(opportunity__is_active=True)
            .values('skill__skill_name', 'skill__category')
            .annotate(
                demand_count=Count('id'),
                avg_required_score=Avg('required_score'),
            )
            .order_by('-demand_count')[:20]
        )
        return Response(list(demand))
