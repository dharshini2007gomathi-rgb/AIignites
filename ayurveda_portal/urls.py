"""Main URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from portal import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include('ayurveda_portal.api_urls')),

    # Public
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/assessment/', views.student_assessment, name='student_assessment'),
    path('student/assessment/concept-test/start/', views.student_start_concept_test, name='student_start_concept_test'),
    path('student/assessment/concept-test/<int:attempt_id>/', views.student_take_concept_test, name='student_take_concept_test'),
    path('student/assessment/concept-test/<int:attempt_id>/result/', views.student_concept_test_result, name='student_concept_test_result'),
    path('student/skills/', views.student_skills, name='student_skills'),
    path('student/opportunities/', views.student_opportunities, name='student_opportunities'),
    path('student/opportunities/<int:opportunity_id>/', views.opportunity_detail, name='opportunity_detail'),
    path('student/opportunities/<int:opportunity_id>/apply/', views.apply_opportunity, name='apply_opportunity'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('student/portfolio/', views.student_portfolio, name='student_portfolio'),
    path('student/settings/', views.student_settings, name='student_settings'),
    path('portfolio/<slug:slug>/', views.public_portfolio, name='public_portfolio'),

    # Industry
    path('industry/dashboard/', views.industry_dashboard, name='industry_dashboard'),
    path('industry/profile/', views.industry_profile, name='industry_profile'),
    path('industry/post/', views.industry_post_opportunity, name='industry_post'),
    path('industry/opportunities/', views.industry_opportunities, name='industry_opportunities'),
    path('industry/applications/', views.industry_applications, name='industry_applications'),

    # Faculty
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/post/', views.faculty_post, name='faculty_post'),
    path('faculty/analytics/', views.faculty_analytics, name='faculty_analytics'),

    # Admin portal
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/opportunities/', views.admin_opportunities, name='admin_opportunities'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
