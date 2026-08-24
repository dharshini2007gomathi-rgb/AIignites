"""
Skill matching and gap analysis algorithms.
Uses weighted cosine similarity for opportunity matching.
"""
import math
import logging
from decimal import Decimal
from django.db.models import Avg

logger = logging.getLogger('skills')


def get_student_skill_map(student):
    """Return dict of skill_id -> score for a student."""
    return {
        ss.skill_id: float(ss.score)
        for ss in student.skills.select_related('skill').all()
    }


def calculate_match_score(student, opportunity):
    """
    Calculate match percentage between student and opportunity using
    weighted cosine similarity on required skills.

    Returns dict with match_score, skill_gaps, and matched_skills.
    """
    student_skills = get_student_skill_map(student)
    requirements = opportunity.required_skills.select_related('skill').all()

    if not requirements.exists():
        return {
            'match_score': 0.0,
            'skill_gaps': [],
            'matched_skills': [],
            'message': 'No skill requirements defined for this opportunity.',
        }

    dot_product = 0.0
    student_magnitude = 0.0
    req_magnitude = 0.0
    skill_gaps = []
    matched_skills = []

    for req in requirements:
        skill_id = req.skill_id
        weight = float(req.weight)
        required = float(req.required_score)
        current = student_skills.get(skill_id, 0.0)

        weighted_current = current * weight
        weighted_required = required * weight

        dot_product += weighted_current * weighted_required
        student_magnitude += weighted_current ** 2
        req_magnitude += weighted_required ** 2

        gap = required - current
        skill_info = {
            'skill_id': skill_id,
            'skill_name': req.skill.skill_name,
            'category': req.skill.category,
            'current_score': round(current, 2),
            'required_score': round(required, 2),
            'gap': round(gap, 2),
            'weight': round(weight, 2),
        }

        if gap > 0:
            skill_gaps.append(skill_info)
        else:
            matched_skills.append(skill_info)

    student_magnitude = math.sqrt(student_magnitude)
    req_magnitude = math.sqrt(req_magnitude)

    if student_magnitude == 0 or req_magnitude == 0:
        match_score = 0.0
    else:
        cosine_sim = dot_product / (student_magnitude * req_magnitude)
        match_score = round(cosine_sim * 100, 2)

    skill_gaps.sort(key=lambda x: x['gap'] * x['weight'], reverse=True)

    logger.debug(
        'Match score for %s vs %s: %.2f%%',
        student.student_id, opportunity.title, match_score
    )

    return {
        'match_score': match_score,
        'skill_gaps': skill_gaps,
        'matched_skills': matched_skills,
        'total_requirements': requirements.count(),
        'gaps_count': len(skill_gaps),
    }


def get_recommended_opportunities(student, limit=10, min_score=30):
    """Rank active opportunities by match score for a student."""
    from opportunities.models import Opportunity

    opportunities = Opportunity.objects.filter(is_active=True).prefetch_related(
        'required_skills__skill'
    )

    recommendations = []
    for opp in opportunities:
        result = calculate_match_score(student, opp)
        if result['match_score'] >= min_score:
            recommendations.append({
                'opportunity': opp,
                'match_score': result['match_score'],
                'skill_gaps': result['skill_gaps'],
            })

    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    return recommendations[:limit]


def get_skill_gap_analysis(student):
    """
    Overall skill gap analysis comparing student scores to
    average industry requirements across all active opportunities.
    """
    from opportunities.models import OpportunitySkill

    student_skills = get_student_skill_map(student)
    industry_reqs = (
        OpportunitySkill.objects
        .filter(opportunity__is_active=True)
        .values('skill_id', 'skill__skill_name', 'skill__category')
        .annotate(avg_required=Avg('required_score'))
    )

    gaps = []
    for req in industry_reqs:
        skill_id = req['skill_id']
        current = student_skills.get(skill_id, 0.0)
        avg_required = float(req['avg_required'] or 0)
        gap = avg_required - current

        if gap > 0:
            gaps.append({
                'skill_id': skill_id,
                'skill_name': req['skill__skill_name'],
                'category': req['skill__category'],
                'current_score': round(current, 2),
                'industry_average': round(avg_required, 2),
                'gap': round(gap, 2),
            })

    gaps.sort(key=lambda x: x['gap'], reverse=True)
    return gaps


def get_recommended_courses(student, limit=10):
    """Recommend courses based on student's largest skill gaps."""
    from courses.models import Course

    gaps = get_skill_gap_analysis(student)
    if not gaps:
        return Course.objects.filter(is_free=True)[:limit]

    gap_skill_ids = [g['skill_id'] for g in gaps[:5]]
    courses = Course.objects.filter(skill_id__in=gap_skill_ids).select_related('skill')

    # Prioritize courses for skills with largest gaps
    gap_order = {sid: idx for idx, sid in enumerate(gap_skill_ids)}
    course_list = list(courses)
    course_list.sort(key=lambda c: gap_order.get(c.skill_id, 999))
    return course_list[:limit]
