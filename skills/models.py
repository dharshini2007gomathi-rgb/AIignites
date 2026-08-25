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
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Active/Verified Skill Score')
    self_assessment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Raw Self-Assessment Score (0-100)')
    validated_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Validated Concept Test Score (0-100)')
    is_validated = models.BooleanField(default=False, help_text='Whether validated through concept test')
    assessment_date = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'skill']

    def __str__(self):
        status_tag = " [Validated]" if self.is_validated else " [Self-Reported]"
        return f"{self.student.student_id} - {self.skill.skill_name}: {self.score}{status_tag}"


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


class ValidationQuestion(models.Model):
    """Domain concept validation questions for objective testing."""

    TYPE_CHOICES = [
        ('mcq', 'Multiple Choice Question'),
        ('case_study', 'Case-Based Clinical Scenario'),
    ]

    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    ANSWER_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    question_id = models.AutoField(primary_key=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='validation_questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mcq')
    case_context = models.TextField(blank=True, default='', help_text='Optional clinical case scenario or background')
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    explanation = models.TextField(blank=True, default='', help_text='Classical Ayurvedic or clinical explanation')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Medium')
    marks = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['skill', 'difficulty', 'question_id']
        verbose_name = 'Validation Question'
        verbose_name_plural = 'Validation Questions'

    def __str__(self):
        return f"[{self.skill.skill_name}] {self.question_text[:60]}..."


class ConceptValidationAttempt(models.Model):
    """An attempt taken by a student on the Career-Path Concept Validation Test."""

    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]

    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='validation_attempts')
    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name='validation_attempts')
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    skill_scores = models.JSONField(default=dict, blank=True, help_text='Skill-wise score breakdown')
    is_latest = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Concept Validation Attempt'
        verbose_name_plural = 'Concept Validation Attempts'

    def __str__(self):
        return f"{self.student.student_id} - Attempt #{self.attempt_number} ({self.career_path.name}): {self.percentage}%"


class ConceptValidationAnswer(models.Model):
    """Recorded student answers to validation questions within an attempt."""

    id = models.AutoField(primary_key=True)
    attempt = models.ForeignKey(ConceptValidationAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ValidationQuestion, on_delete=models.CASCADE, related_name='attempt_answers')
    selected_option = models.CharField(max_length=1, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    score_obtained = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)

    class Meta:
        unique_together = ['attempt', 'question']
        verbose_name = 'Validation Answer'
        verbose_name_plural = 'Validation Answers'

    def __str__(self):
        return f"Attempt #{self.attempt.attempt_number} - Q{self.question.question_id}: {self.selected_option} ({'Correct' if self.is_correct else 'Incorrect'})"
