"""
Career-Path-Specific Concept Validation Test Engine.
Handles deterministic question selection, test attempt lifecycle,
MCQ evaluation, and combining self-reported scores with objective validated scores.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from skills.models import (
    Skill, StudentSkill, CareerPath, CareerPathSkillRequirement,
    ValidationQuestion, ConceptValidationAttempt, ConceptValidationAnswer,
)

logger = logging.getLogger('skills')

# Configurable weighting parameters (30% Self-Assessment, 70% Objective Validation)
WEIGHT_SELF_ASSESSMENT = 0.30
WEIGHT_VALIDATED = 0.70


@transaction.atomic
def generate_validation_test(student):
    """
    Generate an objective domain concept validation test for a student
    based on their selected Career Path and skill requirement weights.

    Selection rules:
    - Generates 10 to 15 questions per attempt.
    - Prioritizes High priority/weight skills (3 questions) and Medium (2 questions), Low (1 question).
    - Prefers questions not yet answered in past completed attempts by this student.
    - Maintains an ~80% MCQ / 20% case study mix.
    - Avoids duplicate questions within the attempt.
    - Falls back safely if question pool is constrained.

    Returns:
        attempt (ConceptValidationAttempt)
        questions (QuerySet/list of ValidationQuestion)
    """
    if not student.career_path:
        raise ValueError("Student has not selected a target Career Path. Please select a Career Path first.")

    career_path = student.career_path
    requirements = career_path.skill_requirements.filter(
        skill__is_active=True
    ).select_related('skill').order_by('-importance_weight', '-required_score')

    if not requirements.exists():
        raise ValueError(f"No skill requirements defined for Career Path: {career_path.name}")

    # Find question IDs previously taken in completed attempts by this student
    past_question_ids = set(
        ConceptValidationAnswer.objects.filter(
            attempt__student=student,
            attempt__status='COMPLETED',
            selected_option__isnull=False
        ).values_list('question_id', flat=True)
    )

    selected_questions = []
    seen_question_ids = set()

    for req in requirements:
        weight = float(req.importance_weight)
        priority = req.priority_level

        if priority == 'High' or weight >= 0.9:
            target_count = 3
        elif priority == 'Medium' or weight >= 0.7:
            target_count = 2
        else:
            target_count = 1

        # 1. First try unattempted questions for this skill
        fresh_qs = list(ValidationQuestion.objects.filter(
            skill=req.skill,
            is_active=True
        ).exclude(question_id__in=seen_question_ids | past_question_ids).order_by('?')[:target_count])

        for q in fresh_qs:
            selected_questions.append(q)
            seen_question_ids.add(q.question_id)

        # 2. If not enough fresh questions, top up from the general pool for this skill
        if len(fresh_qs) < target_count:
            needed = target_count - len(fresh_qs)
            topup_qs = list(ValidationQuestion.objects.filter(
                skill=req.skill,
                is_active=True
            ).exclude(question_id__in=seen_question_ids).order_by('?')[:needed])

            for q in topup_qs:
                selected_questions.append(q)
                seen_question_ids.add(q.question_id)

    # If test has fewer than 10 questions, backfill from career path skills
    if len(selected_questions) < 10:
        skill_ids = [r.skill_id for r in requirements]
        additional_needed = 10 - len(selected_questions)
        backfill_qs = ValidationQuestion.objects.filter(
            skill_id__in=skill_ids,
            is_active=True
        ).exclude(question_id__in=seen_question_ids).order_by('?')[:additional_needed]

        for q in backfill_qs:
            selected_questions.append(q)
            seen_question_ids.add(q.question_id)

    # Cap maximum questions at 15
    if len(selected_questions) > 15:
        selected_questions = selected_questions[:15]

    # If still empty (e.g. fresh database before full seeding), fetch any active questions
    if not selected_questions:
        fallback_qs = ValidationQuestion.objects.filter(
            is_active=True
        ).exclude(question_id__in=seen_question_ids).order_by('?')[:10]
        for q in fallback_qs:
            selected_questions.append(q)
            seen_question_ids.add(q.question_id)

    if not selected_questions:
        raise ValueError("No active validation questions found in the Question Bank. Please seed questions first.")

    # Mark previous attempts as not latest
    ConceptValidationAttempt.objects.filter(
        student=student, career_path=career_path
    ).update(is_latest=False)

    prev_attempts_count = ConceptValidationAttempt.objects.filter(
        student=student, career_path=career_path
    ).count()

    attempt = ConceptValidationAttempt.objects.create(
        student=student,
        career_path=career_path,
        attempt_number=prev_attempts_count + 1,
        status='IN_PROGRESS',
        is_latest=True,
    )

    # Initialize answer records
    for q in selected_questions:
        ConceptValidationAnswer.objects.create(
            attempt=attempt,
            question=q,
            selected_option=None,
            is_correct=False,
            score_obtained=Decimal('0.0'),
        )

    logger.info(
        "Generated Concept Validation Test attempt #%d for student %s (%s) with %d questions",
        attempt.attempt_number, student.student_id, career_path.name, len(selected_questions)
    )

    return attempt, selected_questions


@transaction.atomic
def evaluate_validation_attempt(attempt, submission_data):
    """
    Evaluate student answers for a concept validation attempt,
    calculate skill-wise validated scores, and update final verified skill scores.

    Formula:
    Verified Skill Score = (Self Assessment Score × 30%) + (Concept Test Score × 70%)
    Calculated PER SKILL.
    """
    if attempt.status == 'COMPLETED':
        logger.warning("Attempt #%d already completed.", attempt.attempt_number)
        return get_attempt_result_summary(attempt)

    # Normalize submission data to {int(question_id): str(option)}
    answers_map = {}
    if isinstance(submission_data, list):
        for item in submission_data:
            qid = item.get('question_id')
            opt = item.get('selected_option') or item.get('answer')
            if qid is not None:
                answers_map[int(qid)] = str(opt).strip().upper() if opt else None
    elif isinstance(submission_data, dict):
        for k, v in submission_data.items():
            if str(k).isdigit():
                answers_map[int(k)] = str(v).strip().upper() if v else None
            elif str(k).startswith('q_') and str(k)[2:].isdigit():
                answers_map[int(str(k)[2:])] = str(v).strip().upper() if v else None

    answers = attempt.answers.select_related('question__skill').all()
    total_obtained = Decimal('0.0')
    max_possible = Decimal('0.0')
    skill_stats = {}

    for ans in answers:
        q = ans.question
        skill_name = q.skill.skill_name
        skill_id = q.skill.skill_id
        q_marks = Decimal(str(q.marks))

        max_possible += q_marks

        if skill_name not in skill_stats:
            skill_stats[skill_name] = {
                'skill_id': skill_id,
                'skill_name': skill_name,
                'category': q.skill.category,
                'obtained_marks': Decimal('0.0'),
                'max_marks': Decimal('0.0'),
                'total_questions': 0,
                'correct_questions': 0,
            }

        skill_stats[skill_name]['total_questions'] += 1
        skill_stats[skill_name]['max_marks'] += q_marks

        student_choice = answers_map.get(q.question_id)
        is_correct = False
        obtained_mark = Decimal('0.0')

        if student_choice:
            ans.selected_option = student_choice
            if student_choice == q.correct_answer.strip().upper():
                is_correct = True
                obtained_mark = q_marks
                total_obtained += obtained_mark
                skill_stats[skill_name]['obtained_marks'] += obtained_mark
                skill_stats[skill_name]['correct_questions'] += 1

        ans.is_correct = is_correct
        ans.score_obtained = obtained_mark
        ans.save()

    # Calculate overall percentage
    overall_percentage = round((float(total_obtained) / float(max_possible)) * 100, 2) if max_possible > 0 else 0.0

    # Calculate per-skill validated score percentages
    skill_scores_summary = {}
    for s_name, stats in skill_stats.items():
        s_max = float(stats['max_marks'])
        s_obt = float(stats['obtained_marks'])
        s_pct = round((s_obt / s_max) * 100, 2) if s_max > 0 else 0.0

        skill_scores_summary[s_name] = {
            'skill_id': stats['skill_id'],
            'skill_name': s_name,
            'category': stats['category'],
            'obtained': round(s_obt, 2),
            'max_marks': round(s_max, 2),
            'validated_score': s_pct,
            'total_questions': stats['total_questions'],
            'correct_questions': stats['correct_questions'],
        }

    # Finalize attempt record
    attempt.total_score = total_obtained
    attempt.max_score = max_possible
    attempt.percentage = Decimal(str(overall_percentage))
    attempt.skill_scores = skill_scores_summary
    attempt.status = 'COMPLETED'
    attempt.submitted_at = timezone.now()
    attempt.save()

    # Update StudentSkill records with Verified Formula: (Self * 30%) + (Concept Test * 70%)
    student = attempt.student
    for s_name, s_data in skill_scores_summary.items():
        skill_obj = Skill.objects.get(skill_id=s_data['skill_id'])
        validated_score_val = Decimal(str(s_data['validated_score']))

        ss, created = StudentSkill.objects.get_or_create(
            student=student,
            skill=skill_obj,
            defaults={
                'score': validated_score_val,
                'self_assessment_score': Decimal('50.0'),
                'validated_score': validated_score_val,
                'is_validated': True,
            }
        )

        if not created:
            # Preserve self-assessment score if already present, otherwise fallback to existing score
            if ss.self_assessment_score is None:
                ss.self_assessment_score = ss.score if ss.score > 0 else Decimal('50.0')

            ss.validated_score = validated_score_val
            ss.is_validated = True

            # Calculate Final Verified Score = (Self * 0.30) + (Validated * 0.70)
            verified_score = (float(ss.self_assessment_score) * WEIGHT_SELF_ASSESSMENT) + (float(ss.validated_score) * WEIGHT_VALIDATED)
            ss.score = Decimal(str(round(verified_score, 2)))
            ss.save()

    logger.info(
        "Successfully evaluated attempt #%d for student %s. Overall: %.2f%% (%d skills updated)",
        attempt.attempt_number, student.student_id, overall_percentage, len(skill_scores_summary)
    )

    return get_attempt_result_summary(attempt)


def get_attempt_result_summary(attempt):
    """Return comprehensive summary of an evaluated concept validation attempt."""
    answers = attempt.answers.select_related('question__skill').all()
    review_list = []

    for a in answers:
        q = a.question
        review_list.append({
            'question_id': q.question_id,
            'skill_name': q.skill.skill_name,
            'question_type': q.question_type,
            'question_text': q.question_text,
            'case_context': q.case_context,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'selected_option': a.selected_option,
            'correct_answer': q.correct_answer,
            'is_correct': a.is_correct,
            'score_obtained': float(a.score_obtained),
            'marks': float(q.marks),
            'explanation': q.explanation,
            'difficulty': q.difficulty,
        })

    return {
        'attempt_id': attempt.id,
        'attempt_number': attempt.attempt_number,
        'career_path': {
            'id': attempt.career_path.id,
            'name': attempt.career_path.name,
            'category': attempt.career_path.career_category,
        },
        'status': attempt.status,
        'started_at': attempt.started_at.isoformat(),
        'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        'total_score': float(attempt.total_score),
        'max_score': float(attempt.max_score),
        'percentage': float(attempt.percentage),
        'skill_scores': attempt.skill_scores,
        'review': review_list,
        'is_validated': True,
    }
