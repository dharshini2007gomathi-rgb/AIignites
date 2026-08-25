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


class CareerSkillGapAnalysisTests(TestCase):
    """Unit and API tests for Career-Path-Specific Skill Gap Analysis engine."""

    def setUp(self):
        from skills.models import CareerPath, CareerPathSkillRequirement

        # Create skills
        self.skill_ayurveda = Skill.objects.create(skill_name='Ayurveda Knowledge', category='Ayurveda Knowledge')
        self.skill_research = Skill.objects.create(skill_name='Research Methodology', category='Research')
        self.skill_doc = Skill.objects.create(skill_name='Documentation', category='Documentation')
        self.skill_comm = Skill.objects.create(skill_name='Communication', category='Communication')
        self.skill_digital = Skill.objects.create(skill_name='Digital Skills', category='Digital')

        # Create Career Path
        self.career_path = CareerPath.objects.create(
            name='Ayurvedic Research Scientist',
            career_category='Research & Development',
            description='Leading scientific trials and research in Ayurveda.',
        )

        # Requirements matching user prompt example:
        # Ayurveda Knowledge = 85 (weight 0.9, High)
        # Research Methodology = 90 (weight 1.0, High)
        # Documentation = 85 (weight 0.8, High)
        # Communication = 70 (weight 0.7, Medium)
        # Digital Skills = 75 (weight 0.8, Medium)
        self.req_research = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_research,
            required_score=90.0, importance_weight=1.0, priority_level='High'
        )
        self.req_ayurveda = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_ayurveda,
            required_score=85.0, importance_weight=0.9, priority_level='High'
        )
        self.req_doc = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_doc,
            required_score=85.0, importance_weight=0.8, priority_level='High'
        )
        self.req_digital = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_digital,
            required_score=75.0, importance_weight=0.8, priority_level='Medium'
        )
        self.req_comm = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_comm,
            required_score=70.0, importance_weight=0.7, priority_level='Medium'
        )

        # Create student with Career Path
        self.user = User.objects.create_user('gapstudent', 'gap@test.com', 'pass123')
        self.user.profile.role = 'STUDENT'
        self.user.profile.save()
        self.student = Student.objects.create(
            user=self.user, name='Gap Test Student', email='gap@test.com',
            college='National Institute of Ayurveda', course='BAMS', year=3,
            career_path=self.career_path,
        )

        # Create student scores matching prompt example:
        # Ayurveda Knowledge = 75 (Required = 85, Gap = 10)
        # Research Methodology = 50 (Required = 90, Gap = 40)
        # Documentation = 80 (Required = 85, Gap = 5)
        # Communication = 85 (Required = 70, Gap = 0)
        # Digital Skills = 60 (Required = 75, Gap = 15)
        StudentSkill.objects.create(student=self.student, skill=self.skill_ayurveda, score=75.0)
        StudentSkill.objects.create(student=self.student, skill=self.skill_research, score=50.0)
        StudentSkill.objects.create(student=self.student, skill=self.skill_doc, score=80.0)
        StudentSkill.objects.create(student=self.student, skill=self.skill_comm, score=85.0)
        StudentSkill.objects.create(student=self.student, skill=self.skill_digital, score=60.0)

    def test_gap_calculation_lower_score(self):
        """Student score lower than required calculates exact gap (e.g. 90 - 50 = 40)."""
        from skills.services import get_career_skill_gap_analysis
        result = get_career_skill_gap_analysis(self.student)
        self.assertTrue(result['has_career_path'])

        comp_map = {c['skill_name']: c for c in result['skill_comparisons']}

        # Research Methodology: 50 / 90 -> gap = 40
        self.assertEqual(comp_map['Research Methodology']['skill_gap'], 40.0)
        self.assertEqual(comp_map['Research Methodology']['current_score'], 50.0)
        self.assertEqual(comp_map['Research Methodology']['required_score'], 90.0)

        # Ayurveda Knowledge: 75 / 85 -> gap = 10
        self.assertEqual(comp_map['Ayurveda Knowledge']['skill_gap'], 10.0)

        # Documentation: 80 / 85 -> gap = 5
        self.assertEqual(comp_map['Documentation']['skill_gap'], 5.0)

        # Digital Skills: 60 / 75 -> gap = 15
        self.assertEqual(comp_map['Digital Skills']['skill_gap'], 15.0)

    def test_gap_calculation_higher_score_produces_zero(self):
        """Student score higher than or equal to required produces gap = 0 (no negative gaps)."""
        from skills.services import get_career_skill_gap_analysis
        result = get_career_skill_gap_analysis(self.student)

        comp_map = {c['skill_name']: c for c in result['skill_comparisons']}

        # Communication: 85 / 70 -> gap = 0
        self.assertEqual(comp_map['Communication']['skill_gap'], 0.0)
        self.assertEqual(comp_map['Communication']['skill_status'], 'STRONG')

        # Communication should be in strengths list
        strength_names = [s['skill_name'] for s in result['strengths']]
        self.assertIn('Communication', strength_names)

    def test_career_readiness_score_bounds_and_formula(self):
        """Career Readiness Score stays strictly between 0 and 100% and does not inflate past 100%."""
        from skills.services import get_career_skill_gap_analysis
        result = get_career_skill_gap_analysis(self.student)

        readiness = result['career_readiness_score']
        self.assertGreaterEqual(readiness, 0.0)
        self.assertLessEqual(readiness, 100.0)
        self.assertIn(result['readiness_label'], ['BEGINNER', 'DEVELOPING', 'JOB_READY', 'HIGHLY_READY'])

        # Test with extreme scores (all 100)
        StudentSkill.objects.filter(student=self.student).update(score=100.0)
        max_result = get_career_skill_gap_analysis(self.student)
        self.assertEqual(max_result['career_readiness_score'], 100.0)
        self.assertEqual(max_result['readiness_label'], 'HIGHLY_READY')
        self.assertEqual(max_result['gaps_count'], 0)

        # Test with zero scores
        StudentSkill.objects.filter(student=self.student).update(score=0.0)
        zero_result = get_career_skill_gap_analysis(self.student)
        self.assertEqual(zero_result['career_readiness_score'], 0.0)
        self.assertEqual(zero_result['readiness_label'], 'BEGINNER')
        self.assertEqual(zero_result['strengths_count'], 0)

    def test_importance_weight_affects_readiness(self):
        """Skills with higher importance weight have a greater influence on readiness score."""
        from skills.services import get_career_skill_gap_analysis

        # Setup student with zero scores
        StudentSkill.objects.filter(student=self.student).update(score=0.0)

        # Give full score to Research Methodology (weight 1.0)
        StudentSkill.objects.filter(student=self.student, skill=self.skill_research).update(score=90.0)
        res_high_weight = get_career_skill_gap_analysis(self.student)

        # Reset and give full score to Communication instead (weight 0.7)
        StudentSkill.objects.filter(student=self.student).update(score=0.0)
        StudentSkill.objects.filter(student=self.student, skill=self.skill_comm).update(score=70.0)
        res_low_weight = get_career_skill_gap_analysis(self.student)

        self.assertGreater(
            res_high_weight['career_readiness_score'],
            res_low_weight['career_readiness_score']
        )

    def test_high_gap_plus_high_importance_produces_top_priority(self):
        """Priority score = skill_gap * importance_weight orders high gap + high importance first."""
        from skills.services import get_career_skill_gap_analysis
        result = get_career_skill_gap_analysis(self.student)

        prioritized = result['prioritized_gaps']
        self.assertTrue(len(prioritized) > 0)

        # Top priority should be Research Methodology (gap 40 * weight 1.0 = 40.0)
        top_gap = prioritized[0]
        self.assertEqual(top_gap['skill_name'], 'Research Methodology')
        self.assertEqual(top_gap['priority_score'], 40.0)

        # Verify descending order of priority scores
        priority_scores = [g['priority_score'] for g in prioritized]
        self.assertEqual(priority_scores, sorted(priority_scores, reverse=True))

    def test_student_without_career_path_handling(self):
        """Student without CareerPath returns has_career_path=False with a clear message and no misleading score."""
        from skills.services import get_career_skill_gap_analysis
        user_no_cp = User.objects.create_user('nocp', 'nocp@test.com', 'pass')
        user_no_cp.profile.role = 'STUDENT'
        user_no_cp.profile.save()
        student_no_cp = Student.objects.create(
            user=user_no_cp, name='No CP Student', email='nocp@test.com',
            college='NIA', course='BAMS', year=1,
            career_path=None,
        )

        result = get_career_skill_gap_analysis(student_no_cp)
        self.assertFalse(result['has_career_path'])
        self.assertIsNone(result['career_path'])
        self.assertEqual(result['career_readiness_score'], 0.0)
        self.assertIn('Select your target career path', result['message'])

    def test_api_career_gap_endpoints(self):
        """Test GET /api/students/me/career-gap/ and /api/students/<student_id>/career-gap/ for own data."""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        # Test /api/students/me/career-gap/
        me_resp = client.get('/api/students/me/career-gap/')
        self.assertEqual(me_resp.status_code, 200)
        self.assertTrue(me_resp.data['has_career_path'])
        self.assertEqual(me_resp.data['career_path']['name'], 'Ayurvedic Research Scientist')
        self.assertIn('career_readiness_score', me_resp.data)
        self.assertIn('prioritized_gaps', me_resp.data)
        self.assertIn('strengths', me_resp.data)

        # Test /api/students/<student_id>/career-gap/
        id_resp = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertEqual(id_resp.status_code, 200)
        self.assertEqual(id_resp.data['career_readiness_score'], me_resp.data['career_readiness_score'])

        # Test /api/skills/career-gap/<student_id>/
        skill_resp = client.get(f'/api/skills/career-gap/{self.student.student_id}/')
        self.assertEqual(skill_resp.status_code, 200)
        self.assertEqual(skill_resp.data['career_readiness_score'], me_resp.data['career_readiness_score'])

    def test_student_cannot_access_other_student_career_gap(self):
        """A normal student must NOT be able to access another student's career gap analysis."""
        from rest_framework.test import APIClient
        
        # Create second student
        other_user = User.objects.create_user('other_student', 'other@test.com', 'pass')
        other_user.profile.role = 'STUDENT'
        other_user.profile.save()
        other_student = Student.objects.create(
            user=other_user, name='Other Student', email='other@test.com',
            college='NIA', course='BAMS', year=2,
            career_path=self.career_path,
        )

        client = APIClient()
        client.force_authenticate(user=other_user)

        # Other student tries accessing first student's career gap endpoint
        resp1 = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertEqual(resp1.status_code, 403)
        self.assertIn('error', resp1.data)

        # Other student tries skills alias endpoint
        resp2 = client.get(f'/api/skills/career-gap/{self.student.student_id}/')
        self.assertEqual(resp2.status_code, 403)
        self.assertIn('error', resp2.data)

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated requests to career gap endpoints return 401 or 403."""
        from rest_framework.test import APIClient
        client = APIClient()

        resp_me = client.get('/api/students/me/career-gap/')
        self.assertIn(resp_me.status_code, [401, 403])

        resp_id = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertIn(resp_id.status_code, [401, 403])


    def test_faculty_can_access_student_career_gap(self):
        """Faculty users can access student career gap analysis."""
        from rest_framework.test import APIClient
        
        faculty_user = User.objects.create_user('faculty_user', 'fac@test.com', 'pass')
        faculty_user.profile.role = 'FACULTY'
        faculty_user.profile.save()

        client = APIClient()
        client.force_authenticate(user=faculty_user)

        resp = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['has_career_path'])
        self.assertEqual(resp.data['career_path']['name'], 'Ayurvedic Research Scientist')

    def test_admin_can_access_student_career_gap(self):
        """Admin users can access student career gap analysis."""
        from rest_framework.test import APIClient
        
        admin_user = User.objects.create_user('admin_user', 'admin@test.com', 'pass')
        admin_user.profile.role = 'ADMIN'
        admin_user.profile.save()

        client = APIClient()
        client.force_authenticate(user=admin_user)

        resp = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['career_readiness_score'], 81.97)

    def test_industry_cannot_access_student_career_gap(self):
        """Industry users cannot access student career gap analysis directly."""
        from rest_framework.test import APIClient
        
        ind_user = User.objects.create_user('ind_user', 'ind@test.com', 'pass')
        ind_user.profile.role = 'INDUSTRY'
        ind_user.profile.save()

        client = APIClient()
        client.force_authenticate(user=ind_user)

        resp = client.get(f'/api/students/{self.student.student_id}/career-gap/')
        self.assertEqual(resp.status_code, 403)

    def test_opportunity_cosine_similarity_math_unchanged(self):
        """Verify that calculate_match_score retains its exact weighted cosine similarity formula."""
        from opportunities.models import Industry, Opportunity, OpportunitySkill
        from skills.services import calculate_match_score

        ind_user = User.objects.create_user('opp_ind', 'opp_ind@test.com', 'pass')
        industry = Industry.objects.create(
            user=ind_user, company_name='Ayur Labs', type='Pharma', location='Jaipur'
        )
        opp = Opportunity.objects.create(
            industry=industry, title='Clinical Researcher', type='Research',
            description='Trial investigator', location='Jaipur'
        )
        # Add required skills: Research Methodology (weight 1.0, req 90) & Documentation (weight 0.8, req 80)
        OpportunitySkill.objects.create(opportunity=opp, skill=self.skill_research, required_score=90.0, weight=1.0)
        OpportunitySkill.objects.create(opportunity=opp, skill=self.skill_doc, required_score=80.0, weight=0.8)

        # Student has: Research=50, Doc=80
        # Dot product = (50*1.0)*(90*1.0) + (80*0.8)*(80*0.8) = 4500 + 4096 = 8596
        # Student mag = sqrt((50)^2 + (64)^2) = sqrt(2500 + 4096) = sqrt(6596) = 81.21576
        # Req mag = sqrt((90)^2 + (64)^2) = sqrt(8100 + 4096) = sqrt(12196) = 110.4355
        # Expected cosine = 8596 / (81.21576 * 110.4355) = 8596 / 8969.098 = 0.958401 -> 95.84%
        res = calculate_match_score(self.student, opp)
        self.assertEqual(res['match_score'], 95.84)


class ConceptValidationTestTests(TestCase):
    """Automated tests for Career-Path-Specific Concept Validation Test (Layer 2)."""

    def setUp(self):
        from rest_framework.test import APIClient
        from skills.models import (
            Skill, CareerPath, CareerPathSkillRequirement,
            ValidationQuestion, ConceptValidationAttempt, ConceptValidationAnswer,
            StudentSkill, Assessment,
        )

        self.client = APIClient()

        # Create Skills
        self.skill_clinical = Skill.objects.create(skill_name='Clinical Skills', category='Clinical')
        self.skill_ayurveda = Skill.objects.create(skill_name='Ayurveda Knowledge', category='Ayurveda Knowledge')
        self.skill_panchakarma = Skill.objects.create(skill_name='Panchakarma', category='Clinical')
        self.skill_research = Skill.objects.create(skill_name='Research Methodology', category='Research')

        # Create Career Path
        self.career_path = CareerPath.objects.create(
            name='Ayurvedic Clinical Practitioner',
            career_category='Clinical Practice',
            description='Primary clinical care',
        )

        # Requirements: Clinical Skills (High, 1.0), Ayurveda Knowledge (High, 0.9), Panchakarma (Medium, 0.7)
        CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_clinical,
            required_score=90.0, importance_weight=1.0, priority_level='High'
        )
        CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_ayurveda,
            required_score=85.0, importance_weight=0.9, priority_level='High'
        )
        CareerPathSkillRequirement.objects.create(
            career_path=self.career_path, skill=self.skill_panchakarma,
            required_score=75.0, importance_weight=0.7, priority_level='Medium'
        )

        # Create Questions for each skill
        self.q1_clin = ValidationQuestion.objects.create(
            skill=self.skill_clinical, question_text='Clinical Q1: Nadi Pariksha for Vata?',
            option_a='Sarpa Gati', option_b='Manduka Gati', option_c='Hamsa Gati', option_d='Kaka Gati',
            correct_answer='A', marks=1.0, difficulty='Easy',
        )
        self.q2_clin = ValidationQuestion.objects.create(
            skill=self.skill_clinical, question_text='Clinical Q2: Dashavidha Pariksha Satva?',
            option_a='Mental strength', option_b='Dietary habit', option_c='Body height', option_d='Skin tone',
            correct_answer='A', marks=1.0, difficulty='Medium',
        )
        self.q3_clin = ValidationQuestion.objects.create(
            skill=self.skill_clinical, question_text='Clinical Q3: Pulse for Pitta?',
            option_a='Sarpa', option_b='Manduka Gati', option_c='Hamsa', option_d='Bheka',
            correct_answer='B', marks=1.0, difficulty='Medium',
        )

        self.q1_ayur = ValidationQuestion.objects.create(
            skill=self.skill_ayurveda, question_text='Ayurveda Q1: Trisutra Ayurveda?',
            option_a='Hetu Linga Aushadha', option_b='Vata Pitta Kapha', option_c='Ahara Nidra Brahmacharya', option_d='Rasa Rakta Mamsa',
            correct_answer='A', marks=1.0, difficulty='Easy',
        )
        self.q2_ayur = ValidationQuestion.objects.create(
            skill=self.skill_ayurveda, question_text='Ayurveda Q2: Digestion first stage dosha?',
            option_a='Vata', option_b='Kapha', option_c='Pitta', option_d='Rakta',
            correct_answer='B', marks=1.0, difficulty='Medium',
        )
        self.q3_ayur = ValidationQuestion.objects.create(
            skill=self.skill_ayurveda, question_text='Ayurveda Q3: Meda Dhatu precursor?',
            option_a='Mamsa', option_b='Rasa', option_c='Asthi', option_d='Majja',
            correct_answer='A', marks=1.0, difficulty='Medium',
        )

        self.q1_panch = ValidationQuestion.objects.create(
            skill=self.skill_panchakarma, question_text='Panchakarma Q1: Samyak Snigdha?',
            option_a='Vatanulomana Deeptagni', option_b='Constipation', option_c='Fever', option_d='Thirst',
            correct_answer='A', marks=1.0, difficulty='Medium',
        )
        self.q2_panch = ValidationQuestion.objects.create(
            skill=self.skill_panchakarma, question_text='Panchakarma Q2: Samsarjana Krama start?',
            option_a='Peya', option_b='Mamsa Rasa', option_c='Odana', option_d='Takra',
            correct_answer='A', marks=1.0, difficulty='Medium',
        )

        # Create Students
        self.user = User.objects.create_user('val_student', 'val@demo.com', 'pass123')
        self.user.profile.role = 'STUDENT'
        self.user.profile.email_verified = True
        self.user.profile.save()

        self.student = Student.objects.create(
            user=self.user, name='Validation Student', email='val@demo.com',
            college='Govt Ayurveda College', course='BAMS', year=4,
            career_path=self.career_path, career_goal='Ayurvedic Clinical Practitioner',
        )

        # Self-assessment initial scores
        StudentSkill.objects.create(
            student=self.student, skill=self.skill_clinical,
            score=Decimal('60.0'), self_assessment_score=Decimal('60.0'), is_validated=False
        )
        StudentSkill.objects.create(
            student=self.student, skill=self.skill_ayurveda,
            score=Decimal('80.0'), self_assessment_score=Decimal('80.0'), is_validated=False
        )
        StudentSkill.objects.create(
            student=self.student, skill=self.skill_panchakarma,
            score=Decimal('50.0'), self_assessment_score=Decimal('50.0'), is_validated=False
        )

    def test_self_assessment_still_works_and_preserves_data(self):
        """Self-assessment questionnaire submission continues to work and preserves self_assessment_score."""
        from skills.models import Assessment
        from skills.scoring import process_assessment_submission

        q_item = Assessment.objects.create(
            skill=self.skill_clinical,
            question_text='I can diagnose Nadi accurately',
            question_type='scale', max_score=5, category='Clinical Skills'
        )

        res = process_assessment_submission(self.student, [{'assessment_id': q_item.assessment_id, 'answer': '4'}])
        self.assertEqual(res['responses_saved'], 1)

        ss = StudentSkill.objects.get(student=self.student, skill=self.skill_clinical)
        self.assertEqual(float(ss.self_assessment_score), 80.0)
        self.assertFalse(ss.is_validated)

    def test_concept_validation_attempt_generation_matches_career_path(self):
        """Generating a test attempt retrieves skills required for student target Career Path."""
        from skills.concept_test_engine import generate_validation_test

        attempt, questions = generate_validation_test(self.student)
        self.assertEqual(attempt.student, self.student)
        self.assertEqual(attempt.career_path, self.career_path)
        self.assertEqual(attempt.status, 'IN_PROGRESS')
        self.assertEqual(attempt.attempt_number, 1)

        # Questions should belong to the required skills
        skill_ids = {q.skill_id for q in questions}
        self.assertTrue(self.skill_clinical.skill_id in skill_ids)
        self.assertTrue(self.skill_ayurveda.skill_id in skill_ids)

    def test_mcq_evaluation_correct_and_incorrect_scoring(self):
        """Correct answers award marks, incorrect answers award 0, and attempt gets finalized."""
        from skills.concept_test_engine import generate_validation_test, evaluate_validation_attempt

        attempt, questions = generate_validation_test(self.student)

        # Answer all correctly except the last one
        sub_list = []
        for i, q in enumerate(questions):
            choice = q.correct_answer if i < len(questions) - 1 else 'D'
            sub_list.append({'question_id': q.question_id, 'selected_option': choice})

        res = evaluate_validation_attempt(attempt, sub_list)
        attempt.refresh_from_db()

        self.assertEqual(attempt.status, 'COMPLETED')
        self.assertIsNotNone(attempt.submitted_at)
        self.assertGreater(float(attempt.percentage), 0.0)
        self.assertEqual(len(res['skill_scores']), 3)

    def test_final_verified_score_formula_30_70(self):
        """Final Verified Score correctly calculates (Self * 0.30) + (Validated * 0.70)."""
        from skills.concept_test_engine import generate_validation_test, evaluate_validation_attempt

        # Self-assessment: Clinical=60.0
        # If student gets 100% on Clinical Validation questions:
        # Verified score should be: (60 * 0.30) + (100 * 0.70) = 18 + 70 = 88.0
        attempt, questions = generate_validation_test(self.student)

        # Answer all clinical questions correctly
        sub_list = []
        for q in questions:
            sub_list.append({'question_id': q.question_id, 'selected_option': q.correct_answer})

        evaluate_validation_attempt(attempt, sub_list)

        ss_clin = StudentSkill.objects.get(student=self.student, skill=self.skill_clinical)
        self.assertTrue(ss_clin.is_validated)
        self.assertEqual(float(ss_clin.self_assessment_score), 60.0)
        self.assertEqual(float(ss_clin.validated_score), 100.0)
        self.assertEqual(float(ss_clin.score), 88.0)

    def test_unvalidated_student_profile_status_self_reported(self):
        """Unvalidated student reports SELF_REPORTED status and career readiness uses self-assessment scores."""
        from skills.services import get_career_skill_gap_analysis

        self.assertFalse(self.student.is_skill_validated)
        self.assertEqual(self.student.validation_status, 'SELF_REPORTED')

        gap_data = get_career_skill_gap_analysis(self.student)
        self.assertEqual(gap_data['validation_status'], 'SELF_REPORTED')
        self.assertEqual(gap_data['readiness_source'], 'SELF_ASSESSMENT')
        self.assertFalse(gap_data['is_validated'])

    def test_validated_student_profile_status_validated(self):
        """Validated student reports VALIDATED status and career readiness uses verified scores."""
        from skills.concept_test_engine import generate_validation_test, evaluate_validation_attempt
        from skills.services import get_career_skill_gap_analysis

        attempt, questions = generate_validation_test(self.student)
        sub_list = [{'question_id': q.question_id, 'selected_option': q.correct_answer} for q in questions]
        evaluate_validation_attempt(attempt, sub_list)

        self.student.refresh_from_db()
        self.assertTrue(self.student.is_skill_validated)
        self.assertEqual(self.student.validation_status, 'VALIDATED')

        gap_data = get_career_skill_gap_analysis(self.student)
        self.assertEqual(gap_data['validation_status'], 'VALIDATED')
        self.assertEqual(gap_data['readiness_source'], 'VALIDATED_BENCHMARK')
        self.assertTrue(gap_data['is_validated'])

    def test_multiple_validation_attempts_preserved_with_sequential_numbers(self):
        """Multiple test attempts are preserved and attempt numbers increase sequentially."""
        from skills.models import ConceptValidationAttempt
        from skills.concept_test_engine import generate_validation_test, evaluate_validation_attempt

        att1, q1 = generate_validation_test(self.student)
        evaluate_validation_attempt(att1, [{'question_id': q.question_id, 'selected_option': 'A'} for q in q1])

        att2, q2 = generate_validation_test(self.student)
        evaluate_validation_attempt(att2, [{'question_id': q.question_id, 'selected_option': 'B'} for q in q2])

        attempts = ConceptValidationAttempt.objects.filter(student=self.student).order_by('attempt_number')
        self.assertEqual(attempts.count(), 2)
        self.assertEqual(attempts[0].attempt_number, 1)
        self.assertEqual(attempts[1].attempt_number, 2)
        self.assertFalse(attempts[0].is_latest)
        self.assertTrue(attempts[1].is_latest)

    def test_concept_test_api_endpoints(self):
        """Test API workflow: start test, submit answers, get result, get history."""
        self.client.force_authenticate(user=self.user)

        # 1. Start Test
        resp_start = self.client.post('/api/skills/concept-test/start/')
        self.assertEqual(resp_start.status_code, 201)
        attempt_id = resp_start.data['attempt_id']
        questions = resp_start.data['questions']

        # Ensure correct_answer is NOT exposed in the student test payload
        for q in questions:
            self.assertNotIn('correct_answer', q)
            self.assertNotIn('explanation', q)

        # 2. Submit Test
        sub_payload = {
            'responses': [{'question_id': q['question_id'], 'selected_option': 'A'} for q in questions]
        }
        resp_sub = self.client.post(f'/api/skills/concept-test/{attempt_id}/submit/', sub_payload, format='json')
        self.assertEqual(resp_sub.status_code, 200)

        # 3. Get Result
        resp_res = self.client.get(f'/api/skills/concept-test/{attempt_id}/result/')
        self.assertEqual(resp_res.status_code, 200)
        self.assertEqual(resp_res.data['status'], 'COMPLETED')

        # 4. Get History
        resp_hist = self.client.get('/api/skills/concept-test/history/')
        self.assertEqual(resp_hist.status_code, 200)
        self.assertEqual(resp_hist.data['total_attempts'], 1)

    def test_unauthorized_student_cannot_access_or_submit_another_students_attempt(self):
        """Students cannot submit or access attempts belonging to other students."""
        other_user = User.objects.create_user('other_stu', 'other@demo.com', 'pass123')
        other_user.profile.role = 'STUDENT'
        other_user.profile.save()
        other_student = Student.objects.create(
            user=other_user, name='Other Student', email='other@demo.com',
            college='NIA Jaipur', course='BAMS', year=2,
            career_path=self.career_path
        )

        from skills.concept_test_engine import generate_validation_test
        attempt, questions = generate_validation_test(self.student)

        # other_user tries to submit for self.student's attempt
        self.client.force_authenticate(user=other_user)
        resp = self.client.post(
            f'/api/skills/concept-test/{attempt.id}/submit/',
            {'responses': []},
            format='json'
        )
        self.assertEqual(resp.status_code, 403)

        # other_user tries to view self.student's detailed result
        resp_get = self.client.get(f'/api/skills/concept-test/{attempt.id}/result/')
        self.assertEqual(resp_get.status_code, 403)

    def test_industry_status_visibility_without_raw_answers(self):
        """Industry providers can check validation status without seeing raw questions/answers."""
        ind_user = User.objects.create_user('ind_checker', 'ind_chk@demo.com', 'pass123')
        ind_user.profile.role = 'INDUSTRY'
        ind_user.profile.save()

        self.client.force_authenticate(user=ind_user)
        resp = self.client.get(f'/api/skills/concept-test/status/{self.student.student_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['student_id'], self.student.student_id)
        self.assertIn('validation_status', resp.data)
        self.assertIn('skills_breakdown', resp.data)
        # Verify raw answers are NOT in the payload
        self.assertNotIn('answers', resp.data)
        self.assertNotIn('review', resp.data)





