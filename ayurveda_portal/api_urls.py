"""API URL routing for all apps."""
from django.urls import path

from accounts.api_views import RegisterView, LoginView, LogoutView, ProfileView, VerifyEmailView
from students.api_views import StudentListView, StudentDetailView, StudentSkillsView, StudentPortfolioView
from skills.api_views import (
    SkillListView, SkillDetailView, AssessmentListView,
    AssessmentSubmitView, GapAnalysisView,
    CareerPathListView, CareerPathDetailView,
    StudentCareerGapAnalysisView,
    ConceptTestStartView, ConceptTestSubmitView,
    ConceptTestResultView, ConceptTestHistoryView,
    ConceptTestStatusView,
)
from opportunities.api_views import (
    OpportunityListView, OpportunityDetailView,
    RecommendedOpportunitiesView, MatchScoreView,
)
from applications.api_views import (
    ApplicationListCreateView, ApplicationDetailView, ApplicationStatusUpdateView,
)
from courses.api_views import CourseListView, RecommendedCoursesView
from analytics.api_views import AnalyticsOverviewView, SkillGapsAnalyticsView, IndustryDemandView

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/profile/', ProfileView.as_view(), name='api-profile'),
    path('auth/verify/<str:token>/', VerifyEmailView.as_view(), name='api-verify-email'),

    # Career Paths
    path('career-paths/', CareerPathListView.as_view(), name='api-career-paths'),
    path('career-paths/<slug:slug>/', CareerPathDetailView.as_view(), name='api-career-path-detail'),

    # Students
    path('students/', StudentListView.as_view(), name='api-students'),
    path('students/me/career-gap/', StudentCareerGapAnalysisView.as_view(), name='api-my-career-gap'),
    path('students/<str:student_id>/', StudentDetailView.as_view(), name='api-student-detail'),
    path('students/<str:student_id>/career-gap/', StudentCareerGapAnalysisView.as_view(), name='api-student-career-gap'),
    path('students/<str:student_id>/skills/', StudentSkillsView.as_view(), name='api-student-skills'),
    path('students/<str:student_id>/portfolio/', StudentPortfolioView.as_view(), name='api-student-portfolio'),

    # Skills & Assessments
    path('skills/', SkillListView.as_view(), name='api-skills'),
    path('skills/<int:pk>/', SkillDetailView.as_view(), name='api-skill-detail'),
    path('skills/assess/', AssessmentSubmitView.as_view(), name='api-assess'),
    path('skills/assessments/', AssessmentListView.as_view(), name='api-assessments'),
    path('skills/gap-analysis/<str:student_id>/', GapAnalysisView.as_view(), name='api-gap-analysis'),
    path('skills/career-gap/<str:student_id>/', StudentCareerGapAnalysisView.as_view(), name='api-career-gap-analysis'),

    # Concept Validation Test (Objective Domain Validation Layer)
    path('skills/concept-test/start/', ConceptTestStartView.as_view(), name='api-concept-test-start'),
    path('skills/concept-test/<int:attempt_id>/submit/', ConceptTestSubmitView.as_view(), name='api-concept-test-submit'),
    path('skills/concept-test/<int:attempt_id>/result/', ConceptTestResultView.as_view(), name='api-concept-test-result'),
    path('skills/concept-test/history/', ConceptTestHistoryView.as_view(), name='api-concept-test-history'),
    path('skills/concept-test/status/', ConceptTestStatusView.as_view(), name='api-concept-test-status-me'),
    path('skills/concept-test/status/<str:student_id>/', ConceptTestStatusView.as_view(), name='api-concept-test-status-student'),



    # Opportunities
    path('opportunities/', OpportunityListView.as_view(), name='api-opportunities'),
    path('opportunities/<int:opportunity_id>/', OpportunityDetailView.as_view(), name='api-opportunity-detail'),
    path('opportunities/recommended/<str:student_id>/', RecommendedOpportunitiesView.as_view(), name='api-recommended'),
    path('opportunities/match-score/<str:student_id>/<int:opportunity_id>/', MatchScoreView.as_view(), name='api-match-score'),

    # Applications
    path('applications/', ApplicationListCreateView.as_view(), name='api-applications'),
    path('applications/<int:application_id>/', ApplicationDetailView.as_view(), name='api-application-detail'),
    path('applications/<int:application_id>/status/', ApplicationStatusUpdateView.as_view(), name='api-application-status'),

    # Courses
    path('courses/', CourseListView.as_view(), name='api-courses'),
    path('courses/recommended/<str:student_id>/', RecommendedCoursesView.as_view(), name='api-courses-recommended'),

    # Analytics
    path('analytics/overview/', AnalyticsOverviewView.as_view(), name='api-analytics-overview'),
    path('analytics/skill-gaps/', SkillGapsAnalyticsView.as_view(), name='api-analytics-gaps'),
    path('analytics/industry-demand/', IndustryDemandView.as_view(), name='api-analytics-demand'),
]
