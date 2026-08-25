from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from students.models import Student
from skills.models import Skill, StudentSkill, CareerPath, CareerPathSkillRequirement


class StudentDashboardViewTests(TestCase):
    """Integration tests for Student Dashboard and Skill Profile views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('dashstudent', 'dash@test.com', 'pass123')
        self.user.profile.role = 'STUDENT'
        self.user.profile.save()

        self.career_path = CareerPath.objects.create(
            name='Ayurvedic Clinical Practitioner',
            career_category='Clinical Practice',
            description='Primary clinical role focusing on holistic diagnosis.',
        )

        self.skill = Skill.objects.create(skill_name='Clinical Skills', category='Clinical')
        self.req = CareerPathSkillRequirement.objects.create(
            career_path=self.career_path,
            skill=self.skill,
            required_score=90.0,
            importance_weight=1.0,
            priority_level='High',
        )

        self.student = Student.objects.create(
            user=self.user,
            name='Dashboard Test Student',
            email='dash@test.com',
            college='National Institute of Ayurveda',
            course='BAMS',
            year=3,
            career_path=self.career_path,
        )

        StudentSkill.objects.create(
            student=self.student,
            skill=self.skill,
            score=75.0,
        )

        self.client.force_login(self.user)

    def test_student_dashboard_renders_with_career_path(self):
        """Dashboard renders successfully with Career Skill Gap Analysis section."""
        response = self.client.get('/student/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Career Skill Gap Analysis')
        self.assertContains(response, 'Ayurvedic Clinical Practitioner')
        self.assertContains(response, 'Career Readiness')
        self.assertContains(response, 'careerComparisonChart')
        self.assertIn('career_gap', response.context)
        self.assertTrue(response.context['career_gap']['has_career_path'])

    def test_student_dashboard_renders_without_career_path(self):
        """Dashboard renders prompt when student has no career path."""
        self.student.career_path = None
        self.student.save()

        response = self.client.get('/student/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select your target career path')
        self.assertIn('career_gap', response.context)
        self.assertFalse(response.context['career_gap']['has_career_path'])

    def test_student_skills_page_renders_with_gap_analysis(self):
        """Skills page renders Career Path Benchmarking section alongside standard charts."""
        response = self.client.get('/student/skills/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Career Path Benchmarking')
        self.assertContains(response, 'Skill Radar Chart')
        self.assertContains(response, 'Skill Gaps vs Industry')
        self.assertContains(response, 'careerComparisonChart')

