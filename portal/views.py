"""
Frontend views for the Ayurveda Skill Mapping & Internship Portal.
Handles all role-based dashboard and page rendering.
"""
import json
import logging
from django.db import models
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.permissions import role_required
from accounts.utils import create_user_with_role, send_verification_email, generate_verification_token
from accounts.models import EmailVerificationToken, UserProfile
from accounts.serializers import RegisterSerializer
from students.models import Student
from skills.models import Assessment, Skill, CareerPath
from skills.scoring import process_assessment_submission, get_category_profile
from skills.services import (
    get_recommended_opportunities, calculate_match_score, get_skill_gap_analysis,
    get_recommended_courses, get_career_skill_gap_analysis,
)
from opportunities.models import Opportunity, Industry
from applications.models import Application, Internship
from courses.models import Course

logger = logging.getLogger(__name__)


def get_dashboard_redirect(user):
    """Redirect user to role-appropriate dashboard."""
    if not hasattr(user, 'profile'):
        return '/'
    role = user.profile.role
    redirects = {
        'STUDENT': '/student/dashboard/',
        'INDUSTRY': '/industry/dashboard/',
        'FACULTY': '/faculty/dashboard/',
        'ADMIN': '/admin/dashboard/',
    }
    return redirects.get(role, '/')


# ---- Public Pages ----

def home(request):
    stats = {
        'students': Student.objects.count(),
        'opportunities': Opportunity.objects.filter(is_active=True).count(),
        'industries': Industry.objects.count(),
    }
    return render(request, 'portal/home.html', {'stats': stats})


def about(request):
    return render(request, 'portal/about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'portal/contact.html')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect(request.user))

    if request.method == 'POST':
        serializer = RegisterSerializer(data=request.POST)
        if serializer.is_valid():
            user = serializer.save()
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            login(request, user)
            return redirect(get_dashboard_redirect(user))
        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')

    return render(request, 'portal/register.html')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(get_dashboard_redirect(user))
        messages.error(request, 'Invalid username or password.')

    return render(request, 'portal/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def verify_email_view(request, token):
    verification = get_object_or_404(EmailVerificationToken, token=token, is_used=False)
    verification.user.profile.email_verified = True
    verification.user.profile.save()
    verification.is_used = True
    verification.save()
    messages.success(request, 'Email verified successfully!')
    return redirect('login')


# ---- Student Pages ----

@role_required('STUDENT')
def student_dashboard(request):
    student = request.user.student
    profile = get_category_profile(student)
    applications = student.applications.select_related('opportunity').order_by('-applied_date')[:5]
    recommendations = get_recommended_opportunities(student, limit=5)
    career_gap = get_career_skill_gap_analysis(student)

    # Prepare radar chart data (top 6 categories)
    chart_labels = list(profile.keys())[:6]
    chart_scores = [profile[k]['score'] for k in chart_labels]

    # Prepare Career Benchmark comparison chart data
    comparison_labels = []
    comparison_current_scores = []
    comparison_required_scores = []
    if career_gap.get('has_career_path') and career_gap.get('skill_comparisons'):
        for comp in career_gap['skill_comparisons']:
            comparison_labels.append(comp['skill_name'])
            comparison_current_scores.append(comp['current_score'])
            comparison_required_scores.append(comp['required_score'])

    context = {
        'student': student,
        'profile': profile,
        'applications': applications,
        'recommendations': recommendations,
        'career_gap': career_gap,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores),
        'comparison_labels': json.dumps(comparison_labels),
        'comparison_current_scores': json.dumps(comparison_current_scores),
        'comparison_required_scores': json.dumps(comparison_required_scores),
    }
    return render(request, 'student/dashboard.html', context)


@role_required('STUDENT')
def student_profile(request):
    student = request.user.student
    career_paths = CareerPath.objects.filter(is_active=True).prefetch_related('skill_requirements__skill')

    if request.method == 'POST':
        student.name = request.POST.get('name', student.name)
        student.college = request.POST.get('college', student.college)
        student.course = request.POST.get('course', student.course)
        student.year = int(request.POST.get('year', student.year))
        student.specialization = request.POST.get('specialization', '')
        
        career_path_id = request.POST.get('career_path')
        if career_path_id:
            try:
                cp = CareerPath.objects.get(id=career_path_id, is_active=True)
                student.career_path = cp
                student.career_goal = cp.name
            except CareerPath.DoesNotExist:
                pass
        elif 'career_goal' in request.POST:
            student.career_goal = request.POST.get('career_goal', '')

        student.bio = request.POST.get('bio', '')
        student.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('student_profile')

    return render(request, 'student/profile.html', {
        'student': student,
        'career_paths': career_paths,
    })


from skills.models import (
    Assessment, Skill, CareerPath,
    ConceptValidationAttempt, ConceptValidationAnswer, ValidationQuestion,
)
from skills.concept_test_engine import (
    generate_validation_test, evaluate_validation_attempt, get_attempt_result_summary,
)


@role_required('STUDENT')
def student_assessment(request):
    student = request.user.student
    assessments = Assessment.objects.select_related('skill').order_by('category', 'assessment_id')
    categories = assessments.values_list('category', flat=True).distinct()
    grouped = {}
    for a in assessments:
        grouped.setdefault(a.category, []).append(a)

    validation_attempts = ConceptValidationAttempt.objects.filter(
        student=student
    ).select_related('career_path').order_by('-started_at')

    active_in_progress_attempt = validation_attempts.filter(status='IN_PROGRESS').first()
    latest_completed_attempt = validation_attempts.filter(status='COMPLETED').first()

    if request.method == 'POST':
        responses = []
        for key, value in request.POST.items():
            if key.startswith('q_'):
                assessment_id = int(key.replace('q_', ''))
                responses.append({'assessment_id': assessment_id, 'answer': value})
        if responses:
            result = process_assessment_submission(student, responses)
            messages.success(request, f'Self-Assessment completed! {result["responses_saved"]} responses saved.')
            return redirect('student_assessment')
        messages.error(request, 'Please answer at least one question.')

    return render(request, 'student/assessment.html', {
        'student': student,
        'grouped': grouped,
        'categories': categories,
        'validation_attempts': validation_attempts,
        'active_in_progress_attempt': active_in_progress_attempt,
        'latest_completed_attempt': latest_completed_attempt,
    })


@role_required('STUDENT')
def student_start_concept_test(request):
    student = request.user.student
    if not student.career_path:
        messages.warning(request, 'Please select your target Career Path in your profile before starting the Concept Validation Test.')
        return redirect('student_profile')

    try:
        attempt, questions = generate_validation_test(student)
        messages.info(request, f'Started Concept Validation Test #{attempt.attempt_number} for {student.career_path.name}.')
        return redirect('student_take_concept_test', attempt_id=attempt.id)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('student_assessment')


@role_required('STUDENT')
def student_take_concept_test(request, attempt_id):
    student = request.user.student
    attempt = get_object_or_404(ConceptValidationAttempt, id=attempt_id, student=student)

    if attempt.status == 'COMPLETED':
        return redirect('student_concept_test_result', attempt_id=attempt.id)

    answers = attempt.answers.select_related('question__skill').all()

    if request.method == 'POST':
        submission_dict = {}
        for key, value in request.POST.items():
            if key.startswith('q_'):
                qid = key.replace('q_', '')
                submission_dict[qid] = value

        if not submission_dict:
            messages.error(request, 'Please answer the questions before submitting.')
        else:
            result = evaluate_validation_attempt(attempt, submission_dict)
            messages.success(request, f'Concept Validation Test completed! Score: {result["percentage"]}%. Your Skill Profile has been verified.')
            return redirect('student_concept_test_result', attempt_id=attempt.id)

    return render(request, 'student/concept_test.html', {
        'student': student,
        'attempt': attempt,
        'answers': answers,
    })


@role_required('STUDENT')
def student_concept_test_result(request, attempt_id):
    student = request.user.student
    attempt = get_object_or_404(ConceptValidationAttempt, id=attempt_id, student=student)
    result = get_attempt_result_summary(attempt)
    career_gap = get_career_skill_gap_analysis(student)

    return render(request, 'student/concept_test_result.html', {
        'student': student,
        'attempt': attempt,
        'result': result,
        'career_gap': career_gap,
        'learning_path': career_gap.get('learning_path'),
    })


@role_required('STUDENT')
def student_skills(request):
    student = request.user.student
    profile = get_category_profile(student)
    gaps = get_skill_gap_analysis(student)
    career_gap = get_career_skill_gap_analysis(student)

    labels = list(profile.keys())
    scores = [profile[k]['score'] for k in labels]
    gap_labels = [g['skill_name'] for g in gaps[:6]]
    gap_values = [g['gap'] for g in gaps[:6]]

    # Prepare Career Benchmark comparison chart data
    comparison_labels = []
    comparison_current_scores = []
    comparison_required_scores = []
    if career_gap.get('has_career_path') and career_gap.get('skill_comparisons'):
        for comp in career_gap['skill_comparisons']:
            comparison_labels.append(comp['skill_name'])
            comparison_current_scores.append(comp['current_score'])
            comparison_required_scores.append(comp['required_score'])

    context = {
        'student': student,
        'profile': profile,
        'gaps': gaps,
        'career_gap': career_gap,
        'chart_labels': json.dumps(labels),
        'chart_scores': json.dumps(scores),
        'gap_labels': json.dumps(gap_labels),
        'gap_values': json.dumps(gap_values),
        'comparison_labels': json.dumps(comparison_labels),
        'comparison_current_scores': json.dumps(comparison_current_scores),
        'comparison_required_scores': json.dumps(comparison_required_scores),
    }
    return render(request, 'student/skills.html', context)



@role_required('STUDENT')
def student_opportunities(request):
    student = request.user.student
    opp_type = request.GET.get('type', '').strip()
    state = request.GET.get('state', '').strip()
    location = request.GET.get('location', '').strip()
    data_status = request.GET.get('data_status', '').strip()
    skill_filter = request.GET.get('skill', '').strip()

    opportunities = Opportunity.objects.filter(is_active=True).prefetch_related(
        'required_skills__skill', 'industry', 'faculty'
    )

    if opp_type:
        opportunities = opportunities.filter(type=opp_type)
    if state:
        opportunities = opportunities.filter(
            models.Q(state__iexact=state) | models.Q(location__icontains=state)
        )
    if location:
        opportunities = opportunities.filter(
            models.Q(location__icontains=location) | models.Q(title__icontains=location) | models.Q(description__icontains=location)
        )
    if data_status:
        opportunities = opportunities.filter(data_status=data_status)
    if skill_filter:
        opportunities = opportunities.filter(required_skills__skill__skill_name__icontains=skill_filter).distinct()

    # Check target career path for relevance ranking bonus
    target_skill_ids = set()
    if student.career_path:
        target_skill_ids = set(
            student.career_path.skill_requirements.values_list('skill_id', flat=True)
        )

    opp_list = []
    for opp in opportunities:
        match = calculate_match_score(student, opp)

        # Career alignment relevance bonus for ranking order only
        opp_req_skill_ids = set(opp.required_skills.values_list('skill_id', flat=True))
        overlap_count = len(target_skill_ids.intersection(opp_req_skill_ids)) if target_skill_ids else 0
        career_bonus = min(overlap_count * 2.0, 10.0) if target_skill_ids else 0.0
        ranking_score = min(100.0, match['match_score'] + career_bonus)

        opp_list.append({
            'opportunity': opp,
            'match_score': match['match_score'],  # Exact cosine similarity match percentage
            'ranking_score': ranking_score,
            'career_bonus': career_bonus,
            'is_career_relevant': overlap_count > 0,
            'gaps': match['skill_gaps'],
            'matched_skills': match.get('matched_skills', []),
            'is_verified': match.get('is_verified', False),
            'match_type': match.get('match_type', 'SELF_REPORTED'),
            'match_type_label': match.get('match_type_label', 'Self-Assessment Based Match'),
            'eligibility': match.get('eligibility'),
        })

    # Sort primarily by ranking score, then by pure match score
    opp_list.sort(key=lambda x: (x['ranking_score'], x['match_score']), reverse=True)

    # Dynamic sorted state list from database and common Indian states
    indian_states = [
        'Andhra Pradesh', 'Assam', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
        'Himachal Pradesh', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha',
        'Puducherry', 'Rajasthan', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ]
    db_states = list(Opportunity.objects.filter(is_active=True).exclude(state='').values_list('state', flat=True).distinct())
    combined_states = sorted(list(set(indian_states + [s for s in db_states if s])))

    available_types = Opportunity.TYPE_CHOICES

    context = {
        'opportunities': opp_list,
        'selected_type': opp_type,
        'selected_state': state,
        'selected_location': location,
        'selected_status': data_status,
        'selected_skill': skill_filter,
        'available_states': combined_states,
        'available_types': available_types,
        'total_count': len(opp_list),
        'has_active_filters': bool(opp_type or state or location or data_status or skill_filter),
    }
    return render(request, 'student/opportunities.html', context)



@role_required('STUDENT')
def opportunity_detail(request, opportunity_id):
    student = request.user.student
    opportunity = get_object_or_404(Opportunity, opportunity_id=opportunity_id)
    match = calculate_match_score(student, opportunity)
    has_applied = Application.objects.filter(student=student, opportunity=opportunity).exists()
    courses = get_recommended_courses(student, limit=5)

    return render(request, 'student/opportunity_detail.html', {
        'opportunity': opportunity,
        'match': match,
        'has_applied': has_applied,
        'courses': courses,
    })


@role_required('STUDENT')
def student_applications(request):
    applications = request.user.student.applications.select_related('opportunity').order_by('-applied_date')
    return render(request, 'student/applications.html', {'applications': applications})


@role_required('STUDENT')
@require_http_methods(['POST'])
def apply_opportunity(request, opportunity_id):
    student = request.user.student
    opportunity = get_object_or_404(Opportunity, opportunity_id=opportunity_id)

    if Application.objects.filter(student=student, opportunity=opportunity).exists():
        messages.warning(request, 'You have already applied to this opportunity.')
        return redirect('opportunity_detail', opportunity_id=opportunity_id)

    application = Application.objects.create(
        student=student,
        opportunity=opportunity,
        cover_letter=request.POST.get('cover_letter', ''),
    )
    if 'resume' in request.FILES:
        application.resume = request.FILES['resume']
        application.save()

    messages.success(request, 'Application submitted successfully!')
    return redirect('student_applications')


@role_required('STUDENT')
def student_portfolio(request):
    student = request.user.student
    profile = get_category_profile(student)
    internships = Internship.objects.filter(
        application__student=student
    ).select_related('application__opportunity')

    return render(request, 'student/portfolio.html', {
        'student': student,
        'profile': profile,
        'internships': internships,
    })


def public_portfolio(request, slug):
    """Public shareable portfolio page."""
    student = get_object_or_404(Student, portfolio_slug=slug)
    profile = get_category_profile(student)
    return render(request, 'student/portfolio_public.html', {
        'student': student,
        'profile': profile,
    })


@role_required('STUDENT')
def student_settings(request):
    return render(request, 'student/settings.html')


# ---- Industry Pages ----

@role_required('INDUSTRY')
def industry_dashboard(request):
    industry = request.user.industry
    opportunities = industry.opportunities.filter(is_active=True)
    applications = Application.objects.filter(opportunity__industry=industry).select_related('student', 'opportunity')
    return render(request, 'industry/dashboard.html', {
        'industry': industry,
        'opportunities': opportunities,
        'applications': applications[:10],
        'total_apps': applications.count(),
    })


@role_required('INDUSTRY')
def industry_profile(request):
    industry = request.user.industry
    if request.method == 'POST':
        industry.company_name = request.POST.get('company_name', industry.company_name)
        industry.type = request.POST.get('type', industry.type)
        industry.location = request.POST.get('location', industry.location)
        industry.website = request.POST.get('website', '')
        industry.description = request.POST.get('description', '')
        industry.save()
        messages.success(request, 'Profile updated.')
        return redirect('industry_profile')
    return render(request, 'industry/profile.html', {'industry': industry})


@role_required('INDUSTRY')
def industry_post_opportunity(request):
    skills = Skill.objects.filter(is_active=True)
    if request.method == 'POST':
        from opportunities.models import OpportunitySkill
        opp = Opportunity.objects.create(
            industry=request.user.industry,
            title=request.POST.get('title'),
            type=request.POST.get('type'),
            description=request.POST.get('description'),
            duration=request.POST.get('duration', ''),
            location=request.POST.get('location'),
            stipend_salary=request.POST.get('stipend_salary', ''),
            eligibility=request.POST.get('eligibility', ''),
            deadline=request.POST.get('deadline') or None,
        )
        # Parse skill requirements from form
        for skill in skills:
            score_key = f'skill_score_{skill.skill_id}'
            weight_key = f'skill_weight_{skill.skill_id}'
            if score_key in request.POST and request.POST[score_key]:
                OpportunitySkill.objects.create(
                    opportunity=opp,
                    skill=skill,
                    required_score=float(request.POST[score_key]),
                    weight=float(request.POST.get(weight_key, 1.0)),
                )
        messages.success(request, 'Opportunity posted successfully!')
        return redirect('industry_opportunities')
    return render(request, 'industry/post.html', {'skills': skills})


@role_required('INDUSTRY')
def industry_opportunities(request):
    opportunities = request.user.industry.opportunities.all()
    return render(request, 'industry/opportunities.html', {'opportunities': opportunities})


@role_required('INDUSTRY')
def industry_applications(request):
    applications = Application.objects.filter(
        opportunity__industry=request.user.industry
    ).select_related('student', 'opportunity').order_by('-applied_date')

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')
        app = Application.objects.get(application_id=app_id)
        app.status = new_status
        app.save()
        from accounts.utils import send_application_status_email
        send_application_status_email(app)
        messages.success(request, f'Application status updated to {new_status}.')
        return redirect('industry_applications')

    return render(request, 'industry/applications.html', {'applications': applications})


# ---- Faculty Pages ----

@role_required('FACULTY')
def faculty_dashboard(request):
    faculty = request.user.faculty
    opportunities = faculty.opportunities.all()
    return render(request, 'faculty/dashboard.html', {
        'faculty': faculty,
        'opportunities': opportunities,
    })


@role_required('FACULTY')
def faculty_post(request):
    if request.method == 'POST':
        Opportunity.objects.create(
            faculty=request.user.faculty,
            title=request.POST.get('title'),
            type=request.POST.get('type', 'FDP'),
            description=request.POST.get('description'),
            location=request.POST.get('location'),
            duration=request.POST.get('duration', ''),
            eligibility=request.POST.get('eligibility', ''),
        )
        messages.success(request, 'Opportunity posted!')
        return redirect('faculty_dashboard')
    return render(request, 'faculty/post.html')


@role_required('FACULTY')
def faculty_analytics(request):
    from django.db.models import Count
    total_students = Student.objects.count()
    course_counts = Student.objects.values('course').annotate(count=Count('course'))
    return render(request, 'faculty/analytics.html', {
        'total_students': total_students,
        'course_counts': course_counts,
    })


# ---- Admin Pages ----

@role_required('ADMIN')
def admin_dashboard(request):
    from analytics.api_views import AnalyticsOverviewView
    view = AnalyticsOverviewView()
    stats = view.get(request).data
    return render(request, 'admin_portal/dashboard.html', {'stats': stats})


@role_required('ADMIN')
def admin_users(request):
    profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'admin_portal/users.html', {'profiles': profiles})


@role_required('ADMIN')
def admin_opportunities(request):
    opportunities = Opportunity.objects.all().select_related('industry', 'faculty')
    return render(request, 'admin_portal/opportunities.html', {'opportunities': opportunities})


@role_required('ADMIN')
def admin_analytics(request):
    from analytics.api_views import SkillGapsAnalyticsView, IndustryDemandView
    gaps = SkillGapsAnalyticsView().get(request).data
    demand = IndustryDemandView().get(request).data
    gap_labels = json.dumps([g['skill_name'] for g in gaps[:10]])
    gap_values = json.dumps([g['gap'] for g in gaps[:10]])
    demand_labels = json.dumps([d['skill__skill_name'] for d in demand[:10]])
    demand_values = json.dumps([d['demand_count'] for d in demand[:10]])
    return render(request, 'admin_portal/analytics.html', {
        'gaps': gaps,
        'demand': demand,
        'gap_labels': gap_labels,
        'gap_values': gap_values,
        'demand_labels': demand_labels,
        'demand_values': demand_values,
    })


@role_required('ADMIN')
def admin_settings(request):
    return render(request, 'admin_portal/settings.html')
