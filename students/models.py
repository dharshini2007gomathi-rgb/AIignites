"""
Student profile and portfolio models for BAMS/MD/PhD Ayurveda students.
"""
from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    """Core student profile linked to Django User."""

    COURSE_CHOICES = [
        ('BAMS', 'BAMS'),
        ('MD Ayurveda', 'MD Ayurveda'),
        ('PhD Ayurveda', 'PhD Ayurveda'),
    ]

    student_id = models.CharField(max_length=10, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    college = models.CharField(max_length=300)
    course = models.CharField(max_length=50, choices=COURSE_CHOICES)
    year = models.IntegerField(default=1)
    specialization = models.CharField(max_length=200, blank=True)
    career_goal = models.CharField(max_length=300, blank=True)
    career_path = models.ForeignKey(
        'skills.CareerPath',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )
    registration_date = models.DateField(auto_now_add=True)
    portfolio_slug = models.SlugField(max_length=100, unique=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            last = Student.objects.order_by('-student_id').first()
            if last and last.student_id.startswith('STU'):
                num = int(last.student_id[3:]) + 1
            else:
                num = 1
            self.student_id = f"STU{num:05d}"
        if not self.portfolio_slug:
            self.portfolio_slug = self.student_id.lower()
        super().save(*args, **kwargs)

    @property
    def is_skill_validated(self):
        """Check if student has completed a concept validation test."""
        return self.skills.filter(is_validated=True).exists() or self.validation_attempts.filter(status='COMPLETED').exists()

    @property
    def validation_status(self):
        """Return standardized skill profile status."""
        return 'VALIDATED' if self.is_skill_validated else 'SELF_REPORTED'

    @property
    def latest_validation_attempt(self):
        """Return the latest completed concept validation attempt."""
        return self.validation_attempts.filter(status='COMPLETED').order_by('-submitted_at', '-id').first()


class Certification(models.Model):
    """Student certifications for portfolio."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    credential_url = models.URLField(blank=True)

    def __str__(self):
        return self.title


class Project(models.Model):
    """Student projects for portfolio."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=300, blank=True)
    project_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Achievement(models.Model):
    """Student achievements for portfolio."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
