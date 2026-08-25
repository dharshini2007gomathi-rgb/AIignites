"""
Skill matching and gap analysis algorithms.
Uses weighted cosine similarity for opportunity matching.
Integrates domain concept recommendations and eligibility verification.
"""
import math
import logging
from decimal import Decimal
from django.db.models import Avg

from skills.recommendations import get_concepts_for_skill, generate_personalized_learning_path

logger = logging.getLogger('skills')


def get_student_skill_map(student):
    """Return dict of skill_id -> score for a student."""
    return {
        ss.skill_id: float(ss.score)
        for ss in student.skills.select_related('skill').all()
    }


def check_opportunity_eligibility(student, opportunity):
    """
    Check whether a student meets the skill requirements for a given opportunity.
    Compares the student's active verified/current skill scores against the required scores.

    Returns:
        dict with:
            is_eligible (bool)
            status_label (str)
            is_verified (bool)
            met_skills (list)
            missing_skills (list with required score, current score, gap, and recommended concepts)
            total_requirements (int)
            met_count (int)
    """
    student_skills = get_student_skill_map(student)
    requirements = opportunity.required_skills.select_related('skill').all()
    is_verified = getattr(student, 'is_skill_validated', False)

    met_skills = []
    missing_skills = []

    for req in requirements:
        skill_id = req.skill_id
        skill_name = req.skill.skill_name
        current = student_skills.get(skill_id, 0.0)
        required = float(req.required_score)
        gap = round(required - current, 2)

        skill_info = {
            'skill_id': skill_id,
            'skill_name': skill_name,
            'category': req.skill.category,
            'current_score': round(current, 2),
            'required_score': round(required, 2),
            'gap': max(0.0, gap),
            'weight': float(req.weight),
        }

        if current >= required:
            met_skills.append(skill_info)
        else:
            # Attach recommended domain concepts to learn for missing skill
            concept_info = get_concepts_for_skill(skill_name)
            skill_info['concepts_to_learn'] = concept_info.get('concepts', [])
            skill_info['priority'] = 'High' if gap > 20 else 'Medium'
            missing_skills.append(skill_info)

    is_eligible = (len(missing_skills) == 0) and (requirements.count() > 0)

    if is_eligible:
        if is_verified:
            status_label = "Eligible based on your verified skill profile"
        else:
            status_label = "Eligible based on your self-reported profile"
    else:
        if not requirements.exists():
            status_label = "Open Application (No specific skill prerequisites)"
            is_eligible = True
        else:
            status_label = "Skill gaps to improve before applying"

    return {
        'is_eligible': is_eligible,
        'status_label': status_label,
        'is_verified': is_verified,
        'met_skills': met_skills,
        'missing_skills': missing_skills,
        'total_requirements': requirements.count(),
        'met_count': len(met_skills),
    }


def calculate_match_score(student, opportunity):
    """
    Calculate match percentage between student and opportunity using
    weighted cosine similarity on required skills.

    Maintains 100% exact mathematical formula while adding verification metadata.

    Returns dict with match_score, skill_gaps, matched_skills, is_verified, and eligibility.
    """
    student_skills = get_student_skill_map(student)
    requirements = opportunity.required_skills.select_related('skill').all()
    is_verified = getattr(student, 'is_skill_validated', False)

    if not requirements.exists():
        return {
            'match_score': 0.0,
            'skill_gaps': [],
            'matched_skills': [],
            'total_requirements': 0,
            'gaps_count': 0,
            'is_verified': is_verified,
            'match_type': 'VERIFIED' if is_verified else 'SELF_REPORTED',
            'match_type_label': 'Verified Skill Based Match' if is_verified else 'Self-Assessment Based Match',
            'message': 'No skill requirements defined for this opportunity.',
            'eligibility': {
                'is_eligible': True,
                'status_label': 'Open Application (No prerequisites)',
                'missing_skills': [],
                'met_skills': [],
            }
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
            concept_info = get_concepts_for_skill(req.skill.skill_name)
            skill_info['concepts_to_learn'] = concept_info.get('concepts', [])
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

    eligibility = check_opportunity_eligibility(student, opportunity)

    logger.debug(
        'Match score for %s vs %s: %.2f%% (%s)',
        student.student_id, opportunity.title, match_score,
        'VERIFIED' if is_verified else 'SELF_REPORTED'
    )

    return {
        'match_score': match_score,
        'skill_gaps': skill_gaps,
        'matched_skills': matched_skills,
        'total_requirements': requirements.count(),
        'gaps_count': len(skill_gaps),
        'is_verified': is_verified,
        'match_type': 'VERIFIED' if is_verified else 'SELF_REPORTED',
        'match_type_label': 'Verified Skill Based Match' if is_verified else 'Self-Assessment Based Match',
        'eligibility': eligibility,
    }


def get_recommended_opportunities(student, limit=10, min_score=30):
    """Rank active opportunities by match score for a student, factoring in career path relevance."""
    from opportunities.models import Opportunity

    opportunities = Opportunity.objects.filter(is_active=True).prefetch_related(
        'required_skills__skill'
    )

    # Check if student has target career path skills for relevance alignment
    target_skill_ids = set()
    if student.career_path:
        target_skill_ids = set(
            student.career_path.skill_requirements.values_list('skill_id', flat=True)
        )

    recommendations = []
    for opp in opportunities:
        result = calculate_match_score(student, opp)
        if result['match_score'] >= min_score:
            # Career alignment boost for ranking (without modifying base match_score)
            opp_req_skill_ids = set(opp.required_skills.values_list('skill_id', flat=True))
            overlap_count = len(target_skill_ids.intersection(opp_req_skill_ids)) if target_skill_ids else 0
            career_bonus = min(overlap_count * 2.0, 10.0) if target_skill_ids else 0.0
            adjusted_score = min(100.0, result['match_score'] + career_bonus)

            recommendations.append({
                'opportunity': opp,
                'match_score': result['match_score'],
                'adjusted_score': adjusted_score,
                'career_bonus': career_bonus,
                'skill_gaps': result['skill_gaps'],
                'is_verified': result['is_verified'],
                'match_type': result['match_type'],
                'match_type_label': result['match_type_label'],
                'eligibility': result['eligibility'],
            })

    recommendations.sort(key=lambda x: (x.get('adjusted_score', x['match_score']), x['match_score']), reverse=True)
    return recommendations[:limit]


def get_readiness_label(readiness_score):
    """
    Return descriptive readiness label based on score:
    >= 85: HIGHLY_READY
    >= 70: JOB_READY
    >= 45: DEVELOPING
    < 45: BEGINNER
    """
    if readiness_score >= 85.0:
        return 'HIGHLY_READY'
    elif readiness_score >= 70.0:
        return 'JOB_READY'
    elif readiness_score >= 45.0:
        return 'DEVELOPING'
    return 'BEGINNER'


def determine_skill_status(current_score, required_score, priority_level='Medium'):
    """
    Determine skill status based on requirement achievement ratio and priority.
    - STRONG: Meets or exceeds required benchmark (ratio >= 1.0 or current >= required)
    - ON_TRACK: Achieved >= 75% of required score
    - NEEDS_IMPROVEMENT: Achieved >= 50% of required score
    - CRITICAL_GAP: Below 50% of required score (or high priority with ratio < 0.60)
    """
    if required_score <= 0:
        return 'STRONG'

    ratio = current_score / required_score
    if current_score >= required_score or ratio >= 1.0:
        return 'STRONG'
    elif ratio >= 0.75:
        return 'ON_TRACK'
    elif ratio >= 0.50:
        if priority_level == 'High' and ratio < 0.60:
            return 'CRITICAL_GAP'
        return 'NEEDS_IMPROVEMENT'
    else:
        return 'CRITICAL_GAP'


def get_career_skill_gap_analysis(student):
    """
    Career-Path-Specific Skill Gap Analysis.
    Compares the student's current skill scores against the required skill scores
    defined for their selected CareerPath.

    Calculates:
    - current_score (Active verified score if tested, else self-reported)
    - self_assessment_score
    - validated_score (Objective concept test score)
    - verified_score
    - required_score
    - skill_gap (0 if current >= required, no negative gaps)
    - gap_percentage ((gap / required) * 100)
    - achievement_percentage ((min(current/required, 1.0)) * 100)
    - importance_weight
    - priority_level
    - skill_status ('STRONG', 'ON_TRACK', 'NEEDS_IMPROVEMENT', 'CRITICAL_GAP')
    - priority_score (skill_gap * importance_weight)
    - concepts_to_learn (Domain-specific concepts from recommendations taxonomy)

    Calculates Career Readiness Score:
    - achievement_ratio = min(current_score / required_score, 1.0)
    - career_readiness_score = (sum(achievement_ratio * weight) / sum(weight)) * 100
    - readiness_label ('BEGINNER', 'DEVELOPING', 'JOB_READY', 'HIGHLY_READY')

    Returns structured results with:
    - career_path info
    - career_readiness_score
    - readiness_label
    - skill_comparisons
    - prioritized_gaps
    - strengths
    - learning_path (4-step personalized roadmap)
    """
    if not student.career_path:
        return {
            'has_career_path': False,
            'career_path': None,
            'career_readiness_score': 0.0,
            'readiness_label': None,
            'skill_comparisons': [],
            'prioritized_gaps': [],
            'strengths': [],
            'total_requirements': 0,
            'gaps_count': 0,
            'strengths_count': 0,
            'learning_path': generate_personalized_learning_path(student),
            'message': 'Select your target career path to see your personalized skill gap analysis.',
        }

    career_path = student.career_path
    requirements = career_path.skill_requirements.select_related('skill').all()

    if not requirements.exists():
        return {
            'has_career_path': True,
            'career_path': {
                'id': career_path.id,
                'name': career_path.name,
                'slug': career_path.slug,
                'category': career_path.career_category,
                'description': career_path.description,
            },
            'career_readiness_score': 100.0,
            'readiness_label': 'JOB_READY',
            'skill_comparisons': [],
            'prioritized_gaps': [],
            'strengths': [],
            'total_requirements': 0,
            'gaps_count': 0,
            'strengths_count': 0,
            'learning_path': generate_personalized_learning_path(student),
            'message': 'No skill requirements defined for this Career Path.',
        }

    # Map student scores by skill_id and skill_name with validation details
    student_skills_by_id = {}
    student_skills_by_name = {}
    for ss in student.skills.select_related('skill').all():
        score_val = float(ss.score)
        self_val = float(ss.self_assessment_score) if ss.self_assessment_score is not None else score_val
        val_val = float(ss.validated_score) if ss.validated_score is not None else None
        data_tuple = {
            'score': score_val,
            'self_assessment_score': self_val,
            'validated_score': val_val,
            'verified_score': score_val,
            'is_validated': ss.is_validated,
        }
        student_skills_by_id[ss.skill_id] = data_tuple
        student_skills_by_name[ss.skill.skill_name.lower().strip()] = data_tuple

    skill_comparisons = []
    prioritized_gaps = []
    strengths = []

    total_weighted_achieved = 0.0
    total_weight = 0.0

    for req in requirements:
        skill = req.skill
        skill_id = skill.skill_id
        skill_name = skill.skill_name
        category = skill.category

        s_data = student_skills_by_id.get(
            skill_id,
            student_skills_by_name.get(skill_name.lower().strip(), {
                'score': 0.0,
                'self_assessment_score': 0.0,
                'validated_score': None,
                'verified_score': 0.0,
                'is_validated': False,
            })
        )
        current_score = s_data['score']
        required_score = float(req.required_score)
        importance_weight = float(req.importance_weight)
        priority_level = req.priority_level

        # Calculate gap (do not show negative gaps)
        if current_score >= required_score:
            skill_gap = 0.0
            gap_percentage = 0.0
        else:
            skill_gap = round(required_score - current_score, 2)
            gap_percentage = round((skill_gap / required_score) * 100, 2) if required_score > 0 else 0.0

        # Achievement ratio capped at 1.0
        if required_score > 0:
            achievement_ratio = min(current_score / required_score, 1.0)
        else:
            achievement_ratio = 1.0

        achievement_percentage = round(achievement_ratio * 100, 2)

        # Skill status
        status = determine_skill_status(current_score, required_score, priority_level)

        # Priority score for ranking gaps
        priority_score = round(skill_gap * importance_weight, 2)

        # Accumulate weighted readiness
        total_weighted_achieved += achievement_ratio * importance_weight
        total_weight += importance_weight

        concept_info = get_concepts_for_skill(skill_name)

        comparison_data = {
            'skill_id': skill_id,
            'skill_name': skill_name,
            'category': category,
            'current_score': round(current_score, 2),
            'self_assessment_score': round(s_data['self_assessment_score'], 2),
            'validated_score': round(s_data['validated_score'], 2) if s_data['validated_score'] is not None else None,
            'verified_score': round(s_data['verified_score'], 2),
            'is_validated': s_data['is_validated'],
            'required_score': round(required_score, 2),
            'skill_gap': round(skill_gap, 2),
            'gap_percentage': gap_percentage,
            'achievement_percentage': achievement_percentage,
            'importance_weight': round(importance_weight, 2),
            'priority_level': priority_level,
            'skill_status': status,
            'priority_score': priority_score,
            'concepts_to_learn': concept_info.get('concepts', []),
            'overview': concept_info.get('overview', ''),
        }

        skill_comparisons.append(comparison_data)

        if skill_gap > 0:
            prioritized_gaps.append(comparison_data)
        else:
            strengths.append(comparison_data)

    # Calculate overall Career Readiness Score (0 to 100)
    if total_weight > 0:
        career_readiness_score = round((total_weighted_achieved / total_weight) * 100, 2)
    else:
        career_readiness_score = 0.0

    career_readiness_score = max(0.0, min(100.0, career_readiness_score))
    readiness_label = get_readiness_label(career_readiness_score)

    # Sort prioritized gaps descending by priority_score, then by gap
    prioritized_gaps.sort(key=lambda x: (x['priority_score'], x['skill_gap']), reverse=True)

    # Sort strengths by current_score descending
    strengths.sort(key=lambda x: x['current_score'], reverse=True)

    is_student_validated = getattr(student, 'is_skill_validated', False)
    validation_status = 'VALIDATED' if is_student_validated else 'SELF_REPORTED'
    readiness_source = 'VALIDATED_BENCHMARK' if is_student_validated else 'SELF_ASSESSMENT'
    gap_summary = {
        'career_path': {
            'id': career_path.id,
            'name': career_path.name,
            'category': career_path.career_category,
        },
        'prioritized_gaps': prioritized_gaps,
        'is_validated': is_student_validated,
    }
    learning_path = generate_personalized_learning_path(student, gap_data=gap_summary)

    logger.debug(
        'Career gap analysis for %s (%s): Readiness=%.2f%% (%s), Status=%s, Gaps=%d, Strengths=%d',
        student.student_id, career_path.name, career_readiness_score, readiness_label,
        validation_status, len(prioritized_gaps), len(strengths)
    )

    return {
        'has_career_path': True,
        'career_path': {
            'id': career_path.id,
            'name': career_path.name,
            'slug': career_path.slug,
            'category': career_path.career_category,
            'description': career_path.description,
        },
        'career_readiness_score': career_readiness_score,
        'readiness_label': readiness_label,
        'is_validated': is_student_validated,
        'validation_status': validation_status,
        'readiness_source': readiness_source,
        'skill_comparisons': skill_comparisons,
        'prioritized_gaps': prioritized_gaps,
        'strengths': strengths,
        'total_requirements': len(skill_comparisons),
        'gaps_count': len(prioritized_gaps),
        'strengths_count': len(strengths),
        'learning_path': learning_path,
    }


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

    gap_order = {sid: idx for idx, sid in enumerate(gap_skill_ids)}
    course_list = list(courses)
    course_list.sort(key=lambda c: gap_order.get(c.skill_id, 999))
    return course_list[:limit]
