"""Comprehensive tests for Opportunity database expansion, filtering, and matching."""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework.test import APIClient

from opportunities.models import Industry, Opportunity, OpportunitySkill
from skills.models import Skill, StudentSkill, CareerPath, CareerPathSkillRequirement
from students.models import Student
from skills.services import calculate_match_score, get_recommended_opportunities


class OpportunityDatabaseExpansionTests(TestCase):
    """Test suite verifying opportunity expansion, idempotency, filtering, and match math."""

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()

        # Create student user and student record
        self.user = User.objects.create_user('test_student', 'student@test.com', 'pass123')
        self.user.profile.role = 'STUDENT'
        self.user.profile.save()

        self.student = Student.objects.create(
            user=self.user,
            name='Test Ayurveda Student',
            email='student@test.com',
            college='National Institute of Ayurveda',
            course='BAMS',
            year=3,
        )

        self.client.force_login(self.user)
        self.api_client.force_authenticate(user=self.user)

    def test_seed_creates_at_least_15_opportunities(self):
        """Seed command creates well over the required minimum of 15 opportunities across India."""
        call_command('seed_data')
        total_opps = Opportunity.objects.count()
        self.assertGreaterEqual(
            total_opps, 15,
            f"Expected at least 15 opportunities after seeding, found {total_opps}"
        )
        self.assertGreaterEqual(
            total_opps, 25,
            f"Target was 20-30+ opportunities, found {total_opps}"
        )

    def test_seed_command_idempotent_no_duplicates(self):
        """Running seed_data multiple times does not duplicate records or create integrity errors."""
        call_command('seed_data')
        first_count = Opportunity.objects.count()
        first_skills_count = OpportunitySkill.objects.count()

        # Run again
        call_command('seed_data')
        second_count = Opportunity.objects.count()
        second_skills_count = OpportunitySkill.objects.count()

        self.assertEqual(first_count, second_count, "Running seed_data twice created duplicate opportunities!")
        self.assertEqual(first_skills_count, second_skills_count, "Running seed_data twice created duplicate skills!")

    def test_existing_opportunities_preserved(self):
        """Custom pre-existing opportunities are not deleted when seed command runs."""
        ind_user = User.objects.create_user('custom_ind', 'custom@ind.com', 'pass123')
        industry = Industry.objects.create(
            user=ind_user,
            company_name='Pre-existing Custom Clinic',
            type='Hospital',
            location='Shimla, Himachal Pradesh',
        )
        custom_opp = Opportunity.objects.create(
            industry=industry,
            title='Pre-existing Custom Resident Position',
            type='Job',
            location='Shimla, Himachal Pradesh',
            state='Himachal Pradesh',
            data_status='VERIFIED',
            description='Custom opportunity created before seed',
        )

        call_command('seed_data')

        # Verify our custom opportunity is still in database
        self.assertTrue(
            Opportunity.objects.filter(opportunity_id=custom_opp.opportunity_id).exists(),
            "Pre-existing opportunity was deleted by seed command!"
        )

    def test_geographical_distribution_across_multiple_states(self):
        """Verify opportunities span South, North, West, East, and Central India."""
        call_command('seed_data')

        distinct_states = set(
            Opportunity.objects.filter(is_active=True).exclude(state='').values_list('state', flat=True)
        )

        # Verify representation across all key zones of India
        self.assertIn('Delhi', distinct_states)
        self.assertIn('Uttar Pradesh', distinct_states)
        self.assertIn('Rajasthan', distinct_states)
        self.assertIn('Maharashtra', distinct_states)
        self.assertIn('Gujarat', distinct_states)
        self.assertIn('West Bengal', distinct_states)
        self.assertIn('Odisha', distinct_states)
        self.assertIn('Madhya Pradesh', distinct_states)
        self.assertIn('Tamil Nadu', distinct_states)
        self.assertIn('Kerala', distinct_states)
        self.assertIn('Karnataka', distinct_states)

        self.assertGreaterEqual(len(distinct_states), 10, "Opportunities must cover at least 10 different Indian states/regions.")

    def test_filter_by_state(self):
        """Verify filtering opportunities by Indian states (e.g. Maharashtra, Delhi, Rajasthan)."""
        call_command('seed_data')

        # Test Maharashtra filter in web view
        response_mh = self.client.get('/student/opportunities/?state=Maharashtra')
        self.assertEqual(response_mh.status_code, 200)
        mh_opps = response_mh.context['opportunities']
        self.assertGreater(len(mh_opps), 0)
        for item in mh_opps:
            self.assertEqual(item['opportunity'].state, 'Maharashtra')

        # Test Delhi filter in API
        response_delhi = self.api_client.get('/api/opportunities/?state=Delhi')
        self.assertEqual(response_delhi.status_code, 200)
        results = response_delhi.data['results'] if 'results' in response_delhi.data else response_delhi.data
        self.assertGreater(len(results), 0)
        for opp in results:
            self.assertTrue('Delhi' in opp['state'] or 'Delhi' in opp['location'])

    def test_filter_by_opportunity_type(self):
        """Verify filtering opportunities by opportunity type (Internship, Research, Pharma R&D, etc.)."""
        call_command('seed_data')

        response = self.client.get('/student/opportunities/?type=Research')
        self.assertEqual(response.status_code, 200)
        opps = response.context['opportunities']
        self.assertGreater(len(opps), 0)
        for item in opps:
            self.assertEqual(item['opportunity'].type, 'Research')

    def test_combined_filtering(self):
        """Verify multi-criteria combined filtering (e.g. State = Delhi AND Type = Research)."""
        call_command('seed_data')

        response = self.client.get('/student/opportunities/?state=Delhi&type=Research')
        self.assertEqual(response.status_code, 200)
        opps = response.context['opportunities']
        self.assertGreater(len(opps), 0)
        for item in opps:
            self.assertEqual(item['opportunity'].state, 'Delhi')
            self.assertEqual(item['opportunity'].type, 'Research')

    def test_cosine_similarity_math_unchanged(self):
        """Verify calculate_match_score retains its exact weighted cosine similarity formula."""
        skill_res = Skill.objects.create(skill_name='Research Methodology Test', category='Research')
        skill_doc = Skill.objects.create(skill_name='Documentation Test', category='Documentation')

        StudentSkill.objects.create(student=self.student, skill=skill_res, score=50.0)
        StudentSkill.objects.create(student=self.student, skill=skill_doc, score=80.0)

        ind_user = User.objects.create_user('math_ind', 'math@test.com', 'pass')
        industry = Industry.objects.create(
            user=ind_user, company_name='Math Lab', type='Research', location='Jaipur'
        )
        opp = Opportunity.objects.create(
            industry=industry, title='Trial Lead', type='Research',
            description='Test position', location='Jaipur', state='Rajasthan'
        )
        OpportunitySkill.objects.create(opportunity=opp, skill=skill_res, required_score=90.0, weight=1.0)
        OpportunitySkill.objects.create(opportunity=opp, skill=skill_doc, required_score=80.0, weight=0.8)

        # Dot product = (50*1.0)*(90*1.0) + (80*0.8)*(80*0.8) = 4500 + 4096 = 8596
        # Student magnitude = sqrt((50)^2 + (64)^2) = sqrt(2500 + 4096) = sqrt(6596) = 81.21576
        # Req magnitude = sqrt((90)^2 + (64)^2) = sqrt(8100 + 4096) = sqrt(12196) = 110.4355
        # Expected cosine = 8596 / (81.21576 * 110.4355) = 8596 / 8969.098 = 0.958401 -> 95.84%
        res = calculate_match_score(self.student, opp)
        self.assertEqual(res['match_score'], 95.84)

    def test_career_path_relevance_affects_ranking_only_not_match_percentage(self):
        """Career path relevance can boost ranking position without altering raw cosine match percentage."""
        skill_panc = Skill.objects.create(skill_name='Panchakarma Test', category='Clinical')
        skill_clin = Skill.objects.create(skill_name='Clinical Test', category='Clinical')

        cp = CareerPath.objects.create(
            name='Panchakarma Specialist Test',
            career_category='Clinical Specialization',
            description='Test Path',
        )
        CareerPathSkillRequirement.objects.create(
            career_path=cp, skill=skill_panc, required_score=90.0, importance_weight=1.0, priority_level='High'
        )

        self.student.career_path = cp
        self.student.save()

        # Student has moderate scores
        StudentSkill.objects.create(student=self.student, skill=skill_panc, score=70.0)
        StudentSkill.objects.create(student=self.student, skill=skill_clin, score=70.0)

        ind_user = User.objects.create_user('rank_ind', 'rank@test.com', 'pass')
        ind = Industry.objects.create(user=ind_user, company_name='Rank Org', type='Hospital', location='Mumbai')

        # Opp 1 requires Panchakarma (relevant to career path)
        opp1 = Opportunity.objects.create(
            industry=ind, title='Panchakarma Training', type='Clinical Training',
            location='Mumbai', state='Maharashtra'
        )
        OpportunitySkill.objects.create(opportunity=opp1, skill=skill_panc, required_score=70.0, weight=1.0)

        # Opp 2 requires Clinical (less specific to career path)
        opp2 = Opportunity.objects.create(
            industry=ind, title='General Clinical Training', type='Clinical Training',
            location='Mumbai', state='Maharashtra'
        )
        OpportunitySkill.objects.create(opportunity=opp2, skill=skill_clin, required_score=70.0, weight=1.0)

        # Both have 100% cosine match for their single matching requirement
        res1 = calculate_match_score(self.student, opp1)
        res2 = calculate_match_score(self.student, opp2)
        self.assertEqual(res1['match_score'], 100.0)
        self.assertEqual(res2['match_score'], 100.0)

        # Check view rendering: match_score remains 100.0, but opp1 gets career relevance badge
        response = self.client.get('/student/opportunities/')
        self.assertEqual(response.status_code, 200)
        opps = response.context['opportunities']
        top_opp = opps[0]
        # Opp 1 has career_bonus > 0 and ranking_score > Opp 2
        self.assertEqual(top_opp['opportunity'].title, 'Panchakarma Training')
        self.assertEqual(top_opp['match_score'], 100.0)
        self.assertTrue(top_opp['is_career_relevant'])

    def test_demo_status_displayed_correctly(self):
        """Opportunities with DEMO status render clear demonstration notice and badges."""
        ind_user = User.objects.create_user('demo_ind', 'demo@ind.com', 'pass')
        ind = Industry.objects.create(user=ind_user, company_name='Demo Institute', type='Hospital', location='Pune')
        demo_opp = Opportunity.objects.create(
            industry=ind, title='Demo Fellowship', type='Fellowship',
            location='Pune, Maharashtra', state='Maharashtra', data_status='DEMO',
            description='This is a demonstration record.'
        )

        response = self.client.get('/student/opportunities/?state=Maharashtra')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo Opportunity')
        self.assertContains(response, 'Demo Fellowship')
