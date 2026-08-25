"""
Assessment scoring service - processes questionnaire responses
and updates student skill profiles by category.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger('skills')


def score_response(assessment, answer):
    """
    Score a single assessment response based on question type.
    Scale questions: answer is 1-5, mapped to 0-100.
    Yes/No: Yes=100, No=0.
    Multiple choice: index-based scoring from options JSON.
    """
    qtype = assessment.question_type
    max_score = assessment.max_score

    try:
        if qtype == 'scale':
            value = int(answer)
            value = max(1, min(value, max_score))
            return Decimal(str((value / max_score) * 100))

        elif qtype == 'yes_no':
            return Decimal('100') if answer.lower() in ('yes', 'true', '1') else Decimal('0')

        elif qtype == 'multiple_choice':
            options = assessment.options or []
            if answer.isdigit():
                idx = int(answer)
                if 0 <= idx < len(options):
                    return Decimal(str(((idx + 1) / len(options)) * 100))
            for i, opt in enumerate(options):
                if str(opt).lower() == answer.lower():
                    return Decimal(str(((i + 1) / len(options)) * 100))
            return Decimal('0')

    except (ValueError, TypeError) as e:
        logger.warning('Scoring error for assessment %s: %s', assessment.assessment_id, e)

    return Decimal('0')


@transaction.atomic
def process_assessment_submission(student, responses):
    """
    Process batch of assessment responses.
    responses: list of {'assessment_id': int, 'answer': str}

    Updates StudentAssessmentResponse and recalculates category skill scores.
    """
    from skills.models import Assessment, StudentAssessmentResponse, StudentSkill, Skill

    saved = []
    category_scores = {}

    for item in responses:
        assessment_id = item.get('assessment_id')
        answer = str(item.get('answer', ''))

        try:
            assessment = Assessment.objects.select_related('skill').get(
                assessment_id=assessment_id
            )
        except Assessment.DoesNotExist:
            continue

        score = score_response(assessment, answer)

        StudentAssessmentResponse.objects.update_or_create(
            student=student,
            assessment=assessment,
            defaults={'answer': answer, 'score_obtained': score},
        )
        saved.append({'assessment_id': assessment_id, 'score': float(score)})

        category = assessment.category
        if category not in category_scores:
            category_scores[category] = []
        category_scores[category].append(float(score))

    # Update student skills by category (average of category question scores)
    for category, scores in category_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        raw_self_score = Decimal(str(round(avg_score, 2)))

        skill, _ = Skill.objects.get_or_create(
            skill_name=category,
            defaults={'category': category, 'description': f'{category} skills from assessment'},
        )

        ss, created = StudentSkill.objects.get_or_create(
            student=student,
            skill=skill,
            defaults={
                'score': raw_self_score,
                'self_assessment_score': raw_self_score,
                'is_validated': False,
            }
        )
        if not created:
            ss.self_assessment_score = raw_self_score
            if ss.is_validated and ss.validated_score is not None:
                # Recalculate combined score: 30% self-assessment + 70% validated
                combined = (float(ss.self_assessment_score) * 0.30) + (float(ss.validated_score) * 0.70)
                ss.score = Decimal(str(round(combined, 2)))
            else:
                ss.score = raw_self_score
            ss.save()

    logger.info(
        'Processed %d assessment responses for student %s',
        len(saved), student.student_id
    )

    return {
        'responses_saved': len(saved),
        'category_scores': {
            cat: round(sum(sc) / len(sc), 2) for cat, sc in category_scores.items()
        },
    }


def get_category_profile(student):
    """Get student's skill profile grouped by assessment categories."""
    from skills.models import StudentSkill

    skills = StudentSkill.objects.filter(student=student).select_related('skill')
    profile = {}
    for ss in skills:
        profile[ss.skill.skill_name] = {
            'score': float(ss.score),
            'self_assessment_score': float(ss.self_assessment_score) if ss.self_assessment_score is not None else float(ss.score),
            'validated_score': float(ss.validated_score) if ss.validated_score is not None else None,
            'verified_score': float(ss.score),
            'is_validated': ss.is_validated,
            'category': ss.skill.category,
            'assessment_date': ss.assessment_date.isoformat(),
        }
    return profile
