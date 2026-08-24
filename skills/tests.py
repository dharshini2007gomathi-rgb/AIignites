"""Unit tests for skill matching algorithm and scoring."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from students.models import Student
from skills.models import Skill, StudentSkill, Assessment
from skills.scoring import score_response, process_assessment_submission
from skills.services import calculate_match_score, get_skill_gap_analysis
from opportunities.models import Industry, Opportunity, OpportunitySkill


class ScoringTests(TestCase):
    """Test assessment scoring logic."""

    def setUp(self):
        self.skill = Skill.objects.create(skill_name='Test Skill', category='Technical')
        self.scale_assessment = Assessment.objects.create(
            skill=self.skill,
            question_text='Test scale question',
            question_type='scale',
            max_score=5,
            category='Test Category',
        )
        self.yesno_assessment = Assessment.objects.create(
            skill=self.skill,
            question_text='Test yes/no question',
            question_type='yes_no',
            max_score=1,
            category='Test Category',
        )

    def test_scale_scoring_max(self):
        score = score_response(self.scale_assessment, '5')
        self.assertEqual(score, Decimal('100'))

    def test_scale_scoring_mid(self):
        score = score_response(self.scale_assessment, '3')
        self.assertEqual(score, Decimal('60'))

    def test_yes_no_scoring(self):
        self.assertEqual(score_response(self.yesno_assessment, 'yes'), Decimal('100'))
        self.assertEqual(score_response(self.yesno_assessment, 'no'), Decimal('0'))


class MatchingTests(TestCase):
    """Test weighted cosine similarity matching algorithm."""

    def setUp(self):
        user = User.objects.create_user('teststudent', 'test@test.com', 'pass')
        user.profile.role = 'STUDENT'
        user.profile.save()
        self.student = Student.objects.create(
            user=user, name='Test', email='test@test.com',
            college='Test College', course='BAMS', year=3,
        )

        self.skill1 = Skill.objects.create(skill_name='Clinical Skills', category='Clinical')
        self.skill2 = Skill.objects.create(skill_name='Research', category='Research')

        StudentSkill.objects.create(student=self.student, skill=self.skill1, score=80)
        StudentSkill.objects.create(student=self.student, skill=self.skill2, score=60)

        ind_user = User.objects.create_user('testind', 'ind@test.com', 'pass')
        self.industry = Industry.objects.create(
            user=ind_user, company_name='Test Hospital',
            type='Hospital', location='Delhi',
        )
        self.opportunity = Opportunity.objects.create(
            industry=self.industry,
            title='Test Internship',
            type='Internship',
            description='Test',
            location='Delhi',
        )
        OpportunitySkill.objects.create(
            opportunity=self.opportunity, skill=self.skill1,
            required_score=70, weight=1.0,
        )
        OpportunitySkill.objects.create(
            opportunity=self.opportunity, skill=self.skill2,
            required_score=80, weight=0.8,
        )

    def test_perfect_match_high_score(self):
        """Student exceeding requirements should get high match score."""
        result = calculate_match_score(self.student, self.opportunity)
        self.assertGreater(result['match_score'], 50)
        self.assertIn('skill_gaps', result)
        self.assertIn('matched_skills', result)

    def test_skill_gap_identification(self):
        """Should identify skills where student score is below required."""
        result = calculate_match_score(self.student, self.opportunity)
        gap_skills = [g['skill_name'] for g in result['skill_gaps']]
        # Research required 80, student has 60 - should be a gap
        self.assertIn('Research', gap_skills)

    def test_no_requirements_zero_score(self):
        """Opportunity without requirements returns 0 match."""
        empty_opp = Opportunity.objects.create(
            industry=self.industry,
            title='Empty',
            type='Job',
            description='No skills required',
            location='Mumbai',
        )
        result = calculate_match_score(self.student, empty_opp)
        self.assertEqual(result['match_score'], 0.0)


class AssessmentSubmissionTests(TestCase):
    """Test batch assessment submission and skill profile update."""

    def setUp(self):
        user = User.objects.create_user('assessuser', 'assess@test.com', 'pass')
        self.student = Student.objects.create(
            user=user, name='Assess', email='assess@test.com',
            college='Test', course='BAMS', year=2,
        )
        self.skill = Skill.objects.create(
            skill_name='Ayurveda Knowledge', category='Ayurveda Knowledge',
        )
        self.assessment = Assessment.objects.create(
            skill=self.skill,
            question_text='Test Q1',
            question_type='scale',
            max_score=5,
            category='Ayurveda Knowledge',
        )

    def test_submission_updates_skills(self):
        responses = [{'assessment_id': self.assessment.assessment_id, 'answer': '4'}]
        result = process_assessment_submission(self.student, responses)
        self.assertEqual(result['responses_saved'], 1)
        self.assertTrue(self.student.skills.filter(skill__skill_name='Ayurveda Knowledge').exists())


class CareerPathTests(TestCase):
    """Test CareerPath, CareerPathSkillRequirement, and Student integration."""

    def setUp(self):
        from skills.models import CareerPath, CareerPathSkillRequirement
        self.skill_clinical = Skill.objects.create(skill_name='Clinical Diagnosis', category='Clinical')
        self.skill_research = Skill.objects.create(skill_name='Clinical Research', category='Research')

        self.career_path = CareerPath.objects.create(
            name='Ayurvedic Research Scientist',
            career_category='Research & Development',
            description='Leading scientific trials and research in Ayurveda.',
        )

        self.req1 = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path,
            skill=self.skill_research,
            required_score=90.0,
            importance_weight=1.0,
            priority_level='High',
        )
        self.req2 = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path,
            skill=self.skill_clinical,
            required_score=75.0,
            importance_weight=0.7,
            priority_level='Medium',
        )

    def test_career_path_slug_auto_generation(self):
        self.assertEqual(self.career_path.slug, 'ayurvedic-research-scientist')

    def test_career_path_skill_requirements_relation(self):
        reqs = self.career_path.skill_requirements.all()
        self.assertEqual(reqs.count(), 2)
        top_req = reqs.first()
        self.assertEqual(top_req.skill.skill_name, 'Clinical Research')
        self.assertEqual(float(top_req.required_score), 90.0)

    def test_career_path_skill_requirements_unique_constraint(self):
        """Adding duplicate skill to same career path should raise IntegrityError."""
        from django.db import IntegrityError
        from skills.models import CareerPathSkillRequirement

        with self.assertRaises(IntegrityError):
            CareerPathSkillRequirement.objects.create(
                career_path=self.career_path,
                skill=self.skill_research,  # Duplicate of self.req1
                required_score=80.0,
                importance_weight=0.5,
                priority_level='Low',
            )

    def test_student_career_path_assignment_preserves_custom_career_goal(self):
        """Assigning a career_path must NOT overwrite an existing or custom career_goal."""
        user = User.objects.create_user('cpstudent', 'cp@test.com', 'pass')
        student = Student.objects.create(
            user=user, name='Career Student', email='cp@test.com',
            college='NIA', course='BAMS', year=4,
            career_path=self.career_path,
            career_goal='Start a Panchakarma Clinic in Jaipur',  # Custom aspiration
        )
        self.assertEqual(student.career_path, self.career_path)
        self.assertEqual(student.career_goal, 'Start a Panchakarma Clinic in Jaipur')  # Preserved!
        self.assertIn(student, self.career_path.students.all())

    def test_career_path_api_endpoints(self):
        from django.urls import reverse
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.get('/api/career-paths/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results'] if 'results' in response.data else response.data), 1)

        detail_response = client.get(f'/api/career-paths/{self.career_path.slug}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['name'], 'Ayurvedic Research Scientist')
        self.assertEqual(len(detail_response.data['skill_requirements']), 2)


