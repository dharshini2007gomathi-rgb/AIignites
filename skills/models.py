"""
Skill master data, assessments, and student skill scores.
"""
from django.db import models
from django.utils.text import slugify


class Skill(models.Model):
    """Master list of skills across Ayurveda domains."""

    CATEGORY_CHOICES = [
        ('Technical', 'Technical'),
        ('Clinical', 'Clinical'),
        ('Research', 'Research'),
        ('Soft Skill', 'Soft Skill'),
        ('Professional', 'Professional'),
        ('Digital', 'Digital'),
        ('Ayurveda Knowledge', 'Ayurveda Knowledge'),
        ('Communication', 'Communication'),
        ('Documentation', 'Documentation'),
    ]

    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'skill_name']

    def __str__(self):
        return f"{self.skill_name} ({self.category})"


class CareerPath(models.Model):
    """Predefined Ayurvedic Career Paths with associated skill requirements."""

    CATEGORY_CHOICES = [
        ('Clinical Practice', 'Clinical Practice'),
        ('Clinical Specialization', 'Clinical Specialization'),
        ('Research & Development', 'Research & Development'),
        ('Pharmaceutical & Dravyaguna', 'Pharmaceutical & Dravyaguna'),
        ('Healthcare Management', 'Healthcare Management'),
        ('Public Health', 'Public Health'),
        ('Medical Communications', 'Medical Communications'),
        ('Wellness & Entrepreneurship', 'Wellness & Entrepreneurship'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    career_category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Clinical Practice')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['career_category', 'name']
        verbose_name = 'Career Path'
        verbose_name_plural = 'Career Paths'

    def __str__(self):
        return f"{self.name} ({self.career_category})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CareerPathSkillRequirement(models.Model):
    """Skill proficiency benchmark and weight required for a Career Path."""

    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name='skill_requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='career_path_requirements')
    required_score = models.DecimalField(max_digits=5, decimal_places=2, default=70.0)
    importance_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    priority_level = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='High')

    class Meta:
        unique_together = ['career_path', 'skill']
        constraints = [
            models.UniqueConstraint(fields=['career_path', 'skill'], name='unique_career_path_skill_req'),
        ]
        ordering = ['-importance_weight', '-required_score']
        verbose_name = 'Career Path Skill Requirement'
        verbose_name_plural = 'Career Path Skill Requirements'

    def __str__(self):
        return f"{self.career_path.name} requires {self.skill.skill_name} ({self.required_score}%)"


class StudentSkill(models.Model):
    """Skill scores for each student from assessments."""

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='student_scores')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assessment_date = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'skill']

    def __str__(self):
        return f"{self.student.student_id} - {self.skill.skill_name}: {self.score}"


class Assessment(models.Model):
    """Skill assessment questionnaire items."""

    QUESTION_TYPES = [
        ('scale', 'Scale (1-5)'),
        ('multiple_choice', 'Multiple Choice'),
        ('yes_no', 'Yes/No'),
    ]

    assessment_id = models.AutoField(primary_key=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='assessments')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='scale')
    options = models.JSONField(null=True, blank=True)
    max_score = models.IntegerField(default=5)
    category = models.CharField(max_length=50)

    class Meta:
        ordering = ['category', 'assessment_id']

    def __str__(self):
        return f"{self.category}: {self.question_text[:50]}..."


class StudentAssessmentResponse(models.Model):
    """Student answers to assessment questions."""

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='assessment_responses')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses')
    answer = models.CharField(max_length=500)
    score_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'assessment']

    def __str__(self):
        return f"{self.student.student_id} - Q{self.assessment.assessment_id}"
