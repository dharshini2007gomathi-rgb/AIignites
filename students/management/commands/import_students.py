"""Management command to import synthetic student records from CSV."""
import csv
import random
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from students.models import Student
from skills.models import StudentSkill, Skill


COLLEGES = [
    'National Institute of Ayurveda, Jaipur',
    ' Gujarat Ayurved University, Jamnagar',
    ' Kerala University of Health Sciences',
    ' Rajiv Gandhi University of Health Sciences',
    ' Banaras Hindu University',
    ' Dr. Sarvepalli Radhakrishnan Rajasthan Ayurved University',
    ' Maharashtra University of Health Sciences',
    ' Uttarakhand Ayurved University',
]

COURSES = ['BAMS', 'MD Ayurveda', 'PhD Ayurveda']
SPECIALIZATIONS = ['Kayachikitsa', 'Panchakarma', 'Dravyaguna', 'Shalya Tantra', 'Prasuti Tantra', '']


class Command(BaseCommand):
    help = 'Import synthetic student records from CSV (generates CSV if not found)'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, default='data/synthetic_students.csv')
        parser.add_argument('--count', type=int, default=100, help='Records to generate if CSV missing')
        parser.add_argument('--generate-only', action='store_true', help='Only generate CSV, do not import')

    def handle(self, *args, **options):
        csv_path = options['csv']
        count = options['count']

        if not os.path.exists(csv_path):
            self.stdout.write(f'CSV not found at {csv_path}. Generating {count} records...')
            os.makedirs(os.path.dirname(csv_path) or '.', exist_ok=True)
            self._generate_csv(csv_path, count)

        if options['generate_only']:
            self.stdout.write(self.style.SUCCESS(f'CSV generated at {csv_path}'))
            return

        self._import_csv(csv_path)

    def _generate_csv(self, path, count):
        """Generate synthetic student CSV for bulk import."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'email', 'college', 'course', 'year', 'specialization', 'career_goal'])
            for i in range(1, count + 1):
                course = random.choice(COURSES)
                writer.writerow([
                    f'Student {i}',
                    f'student{i}@synthetic.ayurvedaportal.com',
                    random.choice(COLLEGES).strip(),
                    course,
                    random.randint(1, 5 if course == 'BAMS' else 3),
                    random.choice(SPECIALIZATIONS),
                    random.choice(['Clinical Practice', 'Research', 'Teaching', 'Pharma Industry', 'Wellness']),
                ])
        self.stdout.write(f'  Generated {count} records')

    def _import_csv(self, path):
        """Import students from CSV with bulk_create for performance."""
        skills = list(Skill.objects.filter(is_active=True))
        imported = 0
        batch_size = 500
        students_batch = []

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row['email']
                if User.objects.filter(email=email).exists():
                    continue

                username = email.split('@')[0][:30]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}{counter}'
                    counter += 1

                user = User.objects.create_user(username, email, 'synthetic123')
                user.profile.role = 'STUDENT'
                user.profile.email_verified = True
                user.profile.save()

                student = Student(
                    user=user,
                    name=row['name'],
                    email=email,
                    college=row['college'],
                    course=row['course'],
                    year=int(row.get('year', 1)),
                    specialization=row.get('specialization', ''),
                    career_goal=row.get('career_goal', ''),
                )
                student.save()

                # Assign random skill scores
                for skill in skills[:6]:
                    StudentSkill.objects.create(
                        student=student,
                        skill=skill,
                        score=random.randint(20, 95),
                    )

                imported += 1
                if imported % 100 == 0:
                    self.stdout.write(f'  Imported {imported} students...')

        self.stdout.write(self.style.SUCCESS(f'Imported {imported} students from {path}'))
