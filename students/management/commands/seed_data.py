"""Management command to seed sample data for development and demo."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from students.models import Student
from skills.models import Skill, Assessment, StudentSkill, CareerPath, CareerPathSkillRequirement
from opportunities.models import Industry, Opportunity, OpportunitySkill, Faculty
from courses.models import Course
import random


CAREER_PATHS_DATA = [
    {
        'name': 'Ayurvedic Clinical Practitioner',
        'category': 'Clinical Practice',
        'description': 'Primary clinical role focusing on holistic diagnosis, Tridosha assessment, Kayachikitsa treatment protocols, and OPD/IPD patient care.',
        'skills': [
            ('Clinical Skills', 90, 1.0, 'High'),
            ('Ayurveda Knowledge', 85, 1.0, 'High'),
            ('Kayachikitsa', 85, 0.9, 'High'),
            ('Communication', 80, 0.8, 'High'),
            ('Panchakarma', 75, 0.8, 'Medium'),
            ('Documentation', 75, 0.7, 'Medium'),
            ('Digital Skills', 65, 0.5, 'Low'),
        ],
    },
    {
        'name': 'Panchakarma Specialist',
        'category': 'Clinical Specialization',
        'description': 'Specialized clinical expert conducting classical detoxification and rejuvenation therapies including Vamana, Virechana, Basti, Nasya, and Raktamokshana.',
        'skills': [
            ('Panchakarma', 95, 1.0, 'High'),
            ('Clinical Skills', 90, 1.0, 'High'),
            ('Ayurveda Knowledge', 85, 0.9, 'High'),
            ('Communication', 80, 0.8, 'Medium'),
            ('Documentation', 75, 0.7, 'Medium'),
            ('Digital Skills', 60, 0.5, 'Low'),
        ],
    },
    {
        'name': 'Ayurvedic Research Scientist',
        'category': 'Research & Development',
        'description': 'Leading clinical research, protocol design, scientific validation of formulations, epidemiological studies, and academic publications.',
        'skills': [
            ('Research Methodology', 90, 1.0, 'High'),
            ('Ayurveda Knowledge', 85, 0.9, 'High'),
            ('Documentation', 85, 0.8, 'High'),
            ('Digital Skills', 80, 0.8, 'Medium'),
            ('Dravyaguna', 75, 0.7, 'Medium'),
            ('Communication', 75, 0.7, 'Medium'),
        ],
    },
    {
        'name': 'Ayurvedic Pharmacology / R&D Specialist',
        'category': 'Pharmaceutical & Dravyaguna',
        'description': 'Specialized in Dravyaguna (herbal pharmacology), Bhaishajya Kalpana, herbal quality standardization, phytochemistry, and AYUSH regulatory compliance.',
        'skills': [
            ('Dravyaguna', 95, 1.0, 'High'),
            ('Ayurveda Knowledge', 85, 0.9, 'High'),
            ('Research Methodology', 85, 0.9, 'High'),
            ('Documentation', 80, 0.8, 'Medium'),
            ('Digital Skills', 75, 0.7, 'Medium'),
        ],
    },
    {
        'name': 'Ayurvedic Hospital Administrator',
        'category': 'Healthcare Management',
        'description': 'Directing Ayurvedic healthcare facility operations, NABH accreditation standards, patient workflows, staff coordination, and healthcare management.',
        'skills': [
            ('Documentation', 90, 1.0, 'High'),
            ('Digital Skills', 85, 0.9, 'High'),
            ('Communication', 90, 0.9, 'High'),
            ('Ayurveda Knowledge', 70, 0.6, 'Medium'),
            ('Clinical Skills', 65, 0.5, 'Low'),
        ],
    },
    {
        'name': 'Ayurvedic Public Health Professional',
        'category': 'Public Health',
        'description': 'Designing and implementing community health programs, Swastha Vritta (preventive health) campaigns, epidemic prevention, and AYUSH wellness initiatives.',
        'skills': [
            ('Communication', 90, 1.0, 'High'),
            ('Ayurveda Knowledge', 85, 0.9, 'High'),
            ('Documentation', 80, 0.8, 'Medium'),
            ('Digital Skills', 75, 0.7, 'Medium'),
            ('Research Methodology', 70, 0.7, 'Medium'),
        ],
    },
    {
        'name': 'Ayurvedic Medical Content and Research Specialist',
        'category': 'Medical Communications',
        'description': 'Authoring clinical monographs, peer-reviewed medical publications, instructional curricula, medical copywriting, and digital health education.',
        'skills': [
            ('Ayurveda Knowledge', 90, 1.0, 'High'),
            ('Documentation', 90, 1.0, 'High'),
            ('Communication', 85, 0.8, 'High'),
            ('Research Methodology', 80, 0.8, 'High'),
            ('Digital Skills', 80, 0.8, 'Medium'),
        ],
    },
    {
        'name': 'Ayurvedic Wellness Entrepreneur',
        'category': 'Wellness & Entrepreneurship',
        'description': 'Founding and operating integrative health centers, holistic wellness retreats, direct-to-consumer Ayurvedic ventures, and consultancy services.',
        'skills': [
            ('Communication', 90, 1.0, 'High'),
            ('Digital Skills', 85, 0.9, 'High'),
            ('Ayurveda Knowledge', 80, 0.9, 'High'),
            ('Panchakarma', 70, 0.7, 'Medium'),
            ('Clinical Skills', 70, 0.7, 'Medium'),
        ],
    },
]


# Assessment questions by category (50 total)
ASSESSMENT_DATA = {
    'Ayurveda Knowledge': [
        'I can explain the Tridosha (Vata, Pitta, Kapha) theory comprehensively.',
        'I understand the concept of Agni and its role in digestion and metabolism.',
        'I can describe the Panchakarma procedures and their indications.',
        'I am familiar with major Ayurvedic texts (Charaka Samhita, Sushruta Samhita).',
        'I can identify common Ayurvedic herbs and their properties (Dravyaguna).',
        'I understand Rasayana therapy and its clinical applications.',
        'I can explain the concept of Prakriti and Vikriti assessment.',
        'I am knowledgeable about Ayurvedic pharmacology (Bhaishajya Kalpana).',
        'I understand the relationship between Ritu (seasons) and health.',
        'I can apply Ayurvedic diagnostic methods (Nadi Pariksha, Darshan, Sparshan).',
    ],
    'Clinical Skills': [
        'I can perform a complete Ayurvedic patient examination.',
        'I am confident in prescribing basic Ayurvedic treatments.',
        'I can conduct Panchakarma preparatory procedures (Snehana, Swedana).',
        'I have experience with Ayurvedic outpatient department work.',
        'I can prepare and administer common Ayurvedic formulations.',
        'I am skilled in Ayurvedic pulse diagnosis (Nadi Pariksha).',
        'I can manage common diseases using Ayurvedic protocols.',
        'I have assisted in Ayurvedic surgical procedures (Shalya Tantra).',
        'I can perform Ayurvedic therapies (Abhyanga, Shirodhara, etc.).',
        'I maintain proper clinical documentation and patient records.',
    ],
    'Research Methodology': [
        'I understand research design methods relevant to Ayurveda.',
        'I can conduct literature reviews on Ayurvedic topics.',
        'I am familiar with evidence-based Ayurveda research approaches.',
        'I can use statistical tools for research data analysis.',
        'I understand ethical guidelines for clinical research.',
        'I can write research proposals and grant applications.',
        'I have experience with clinical trial methodology.',
        'I can critically evaluate published Ayurveda research papers.',
    ],
    'Communication': [
        'I can effectively communicate Ayurvedic concepts to patients.',
        'I am comfortable presenting at academic conferences.',
        'I can write clear and professional medical reports.',
        'I work well in interdisciplinary healthcare teams.',
        'I can explain treatment plans in simple language to patients.',
        'I am proficient in patient counseling and health education.',
        'I can communicate effectively in English and regional languages.',
    ],
    'Documentation': [
        'I maintain accurate and complete patient case records.',
        'I can write proper discharge summaries and referral letters.',
        'I follow standard medical documentation protocols.',
        'I am skilled in creating treatment protocols and SOPs.',
        'I can prepare academic papers and case study reports.',
        'I maintain organized research data and lab notebooks.',
        'I understand medico-legal aspects of documentation.',
    ],
    'Digital Skills': [
        'I am proficient in using hospital/clinic management software.',
        'I can use telemedicine platforms for patient consultations.',
        'I am comfortable with electronic health record (EHR) systems.',
        'I can use data analysis tools (Excel, SPSS, R basics).',
        'I am familiar with Ayurveda digital databases and resources.',
        'I can create presentations and educational digital content.',
        'I understand health informatics and digital health trends.',
        'I can use online research databases (PubMed, AYUSH Portal).',
    ],
}

SKILLS_DATA = [
    ('Ayurveda Knowledge', 'Technical'),
    ('Clinical Skills', 'Clinical'),
    ('Research Methodology', 'Research'),
    ('Communication', 'Soft Skill'),
    ('Documentation', 'Professional'),
    ('Digital Skills', 'Digital'),
    ('Panchakarma', 'Clinical'),
    ('Dravyaguna', 'Technical'),
    ('Kayachikitsa', 'Clinical'),
    ('Shalya Tantra', 'Clinical'),
]

COURSES_DATA = [
    ('Introduction to Tridosha Theory', 'Ayurveda Knowledge', 'Beginner', 'AYUSH Portal', True),
    ('Advanced Panchakarma Techniques', 'Clinical Skills', 'Advanced', 'NIA Jaipur', False),
    ('Research Methods in Ayurveda', 'Research Methodology', 'Intermediate', 'MoA Research Cell', True),
    ('Clinical Documentation Standards', 'Documentation', 'Beginner', 'NABH India', True),
    ('Digital Health for Ayurveda Practitioners', 'Digital Skills', 'Intermediate', 'e-Ayush', True),
    ('Patient Communication Skills', 'Communication', 'Beginner', 'Coursera', True),
    ('Evidence-Based Ayurveda', 'Research Methodology', 'Advanced', 'PubMed Central', True),
    ('Herbal Pharmacology (Dravyaguna)', 'Ayurveda Knowledge', 'Intermediate', 'Gujarat Ayurved University', False),
    ('Nadi Pariksha Masterclass', 'Clinical Skills', 'Advanced', 'Kerala Ayurveda Academy', False),
    ('Medical Statistics with R', 'Digital Skills', 'Intermediate', 'SWAYAM', True),
]

OPPORTUNITIES_DATA = [
    ('Ayurveda Intern - OPD', 'Internship', 'Kerala Ayurveda Hospital', 'Kochi, Kerala', '3 months', '₹8,000/month'),
    ('Research Associate - Clinical Trials', 'Research', 'Central Council for Research in Ayurveda', 'New Delhi', '6 months', '₹15,000/month'),
    ('Junior Ayurvedic Physician', 'Job', 'Patanjali Ayurved', 'Haridwar, Uttarakhand', 'Full-time', '₹4-6 LPA'),
    ('Panchakarma Therapist Intern', 'Internship', 'Ayurveda Wellness Center', 'Goa', '2 months', '₹5,000/month'),
    ('Pharmacovigilance Associate', 'Job', 'Dabur Research Foundation', 'Ghaziabad', 'Full-time', '₹3-5 LPA'),
]


class Command(BaseCommand):
    help = 'Seed database with sample skills, assessments, courses, career paths, and demo users'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Create skills
        skills = {}
        for name, category in SKILLS_DATA:
            skill, _ = Skill.objects.get_or_create(
                skill_name=name,
                defaults={'category': category, 'description': f'{name} competency skill'},
            )
            skills[name] = skill
        self.stdout.write(f'  Created {len(skills)} skills')

        # Create Career Paths and Skill Requirements
        career_paths_created = 0
        career_path_map = {}
        for cp_data in CAREER_PATHS_DATA:
            cp, _ = CareerPath.objects.get_or_create(
                name=cp_data['name'],
                defaults={
                    'career_category': cp_data['category'],
                    'description': cp_data['description'],
                    'is_active': True,
                },
            )
            career_path_map[cp_data['name']] = cp
            career_paths_created += 1

            for s_name, req_score, weight, priority in cp_data['skills']:
                skill = skills.get(s_name)
                if skill:
                    CareerPathSkillRequirement.objects.update_or_create(
                        career_path=cp,
                        skill=skill,
                        defaults={
                            'required_score': req_score,
                            'importance_weight': weight,
                            'priority_level': priority,
                        },
                    )

        self.stdout.write(f'  Created {career_paths_created} Career Paths with competency requirements')

        # Create assessment questions
        count = 0
        for category, questions in ASSESSMENT_DATA.items():
            skill = skills.get(category, list(skills.values())[0])
            for q_text in questions:
                Assessment.objects.get_or_create(
                    question_text=q_text,
                    defaults={
                        'skill': skill,
                        'question_type': 'scale',
                        'max_score': 5,
                        'category': category,
                    },
                )
                count += 1
        self.stdout.write(f'  Created {count} assessment questions')

        # Create courses
        for name, skill_name, level, provider, is_free in COURSES_DATA:
            skill = skills.get(skill_name)
            if skill:
                Course.objects.get_or_create(
                    course_name=name,
                    defaults={
                        'skill': skill,
                        'level': level,
                        'provider': provider,
                        'link': f'https://example.com/courses/{name.lower().replace(" ", "-")}',
                        'duration': '4 weeks',
                        'is_free': is_free,
                    },
                )
        self.stdout.write(f'  Created {len(COURSES_DATA)} courses')

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@ayurvedaportal.com', 'admin123')
            admin_user.profile.role = 'ADMIN'
            admin_user.profile.email_verified = True
            admin_user.profile.save()
            self.stdout.write('  Created admin user (admin/admin123)')

        # Create demo industry
        if not User.objects.filter(username='demo_industry').exists():
            ind_user = User.objects.create_user('demo_industry', 'industry@demo.com', 'demo123')
            ind_user.profile.role = 'INDUSTRY'
            ind_user.profile.email_verified = True
            ind_user.profile.save()
            industry = Industry.objects.create(
                user=ind_user,
                company_name='Kerala Ayurveda Hospital',
                type='Hospital',
                location='Kochi, Kerala',
                website='https://example.com',
                verified_status=True,
            )

            for title, otype, company, location, duration, stipend in OPPORTUNITIES_DATA:
                opp = Opportunity.objects.create(
                    industry=industry,
                    title=title,
                    type=otype,
                    description=f'Join our team for {title}. Great learning opportunity for Ayurveda students.',
                    location=location,
                    duration=duration,
                    stipend_salary=stipend,
                    eligibility='BAMS students in 3rd year or above',
                )
                # Add skill requirements
                for skill_name, skill in list(skills.items())[:4]:
                    OpportunitySkill.objects.create(
                        opportunity=opp,
                        skill=skill,
                        required_score=random.randint(40, 80),
                        weight=round(random.uniform(0.5, 1.0), 2),
                    )

            self.stdout.write('  Created demo industry with opportunities')

        # Create demo student
        if not User.objects.filter(username='demo_student').exists():
            stu_user = User.objects.create_user('demo_student', 'student@demo.com', 'demo123')
            stu_user.profile.role = 'STUDENT'
            stu_user.profile.email_verified = True
            stu_user.profile.save()
            demo_cp = career_path_map.get('Ayurvedic Clinical Practitioner')
            student = Student.objects.create(
                user=stu_user,
                name='Demo Student',
                email='student@demo.com',
                college='National Institute of Ayurveda',
                course='BAMS',
                year=3,
                specialization='Kayachikitsa',
                career_path=demo_cp,
                career_goal='Ayurvedic Clinical Practitioner',
            )
            # Add sample skill scores
            for skill_name, skill in skills.items():
                StudentSkill.objects.create(
                    student=student,
                    skill=skill,
                    score=random.randint(30, 90),
                )
            self.stdout.write('  Created demo student (demo_student/demo123)')
        else:
            # Update demo student career path if missing
            student = Student.objects.filter(user__username='demo_student').first()
            if student and not student.career_path:
                demo_cp = career_path_map.get('Ayurvedic Clinical Practitioner')
                student.career_path = demo_cp
                student.career_goal = demo_cp.name if demo_cp else 'Ayurvedic Clinical Practitioner'
                student.save()

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

