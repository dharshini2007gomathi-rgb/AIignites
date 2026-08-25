"""
Industry, faculty, and opportunity posting models.
"""
from django.contrib.auth.models import User
from django.db import models
from skills.models import Skill


class Industry(models.Model):
    """Companies and organizations posting opportunities."""

    TYPE_CHOICES = [
        ('Hospital', 'Hospital'),
        ('Pharma', 'Pharma'),
        ('Research', 'Research'),
        ('Wellness Center', 'Wellness Center'),
        ('Startup', 'Startup'),
    ]

    industry_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='industry')
    company_name = models.CharField(max_length=300)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    location = models.CharField(max_length=200)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    verified_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Industries'

    def __str__(self):
        return self.company_name


class Faculty(models.Model):
    """College faculty posting FDP and research opportunities."""

    faculty_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty')
    name = models.CharField(max_length=200)
    college = models.CharField(max_length=300)
    department = models.CharField(max_length=200, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.college}"


class Opportunity(models.Model):
    """Internships, jobs, FDPs, and research positions."""

    TYPE_CHOICES = [
        ('Internship', 'Internship'),
        ('Job', 'Full-Time Job'),
        ('Research', 'Research Opportunity'),
        ('Clinical Training', 'Clinical Training'),
        ('Industry Training', 'Industry Training'),
        ('Fellowship', 'Fellowship'),
        ('Ayurvedic Wellness', 'Ayurvedic Wellness Opportunity'),
        ('Academic Collaboration', 'Academic / Research Collaboration'),
        ('FDP', 'Faculty Development Program (FDP)'),
        ('Pharma R&D', 'Pharmaceutical / R&D Opportunity'),
        ('Hospital Clinical', 'Hospital / Clinical Opportunity'),
        ('Hospital Admin', 'Hospital / Healthcare Administration'),
        ('Medical Content', 'Medical Content & Documentation Opportunity'),
        ('Public Health', 'Public Health Opportunity'),
        ('Startup Support', 'Entrepreneurship / Startup Support Opportunity'),
    ]

    DATA_STATUS_CHOICES = [
        ('DEMO', 'Demo Opportunity'),
        ('NEEDS_VERIFICATION', 'Verify Availability'),
        ('VERIFIED', 'Verified Opportunity'),
    ]

    opportunity_id = models.AutoField(primary_key=True)
    industry = models.ForeignKey(
        Industry, on_delete=models.CASCADE, related_name='opportunities',
        null=True, blank=True
    )
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, related_name='opportunities',
        null=True, blank=True
    )
    title = models.CharField(max_length=300)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField()
    duration = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=100, blank=True, default='', help_text='State or Region')
    data_status = models.CharField(
        max_length=30,
        choices=DATA_STATUS_CHOICES,
        default='NEEDS_VERIFICATION',
        help_text='Indicates data verification status.'
    )
    stipend_salary = models.CharField(max_length=100, blank=True, null=True)
    eligibility = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    posted_date = models.DateField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_date']
        verbose_name_plural = 'Opportunities'

    def __str__(self):
        return self.title

    @property
    def posted_by(self):
        if self.industry:
            return self.industry.company_name
        if self.faculty:
            return self.faculty.name
        return 'Unknown'

    @property
    def status_label(self):
        return dict(self.DATA_STATUS_CHOICES).get(self.data_status, self.data_status)

    @property
    def status_badge_class(self):
        if self.data_status == 'VERIFIED':
            return 'bg-success'
        elif self.data_status == 'DEMO':
            return 'bg-info text-dark'
        return 'bg-warning text-dark'



class OpportunitySkill(models.Model):
    """Required skills and weights for each opportunity."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='required_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='opportunity_requirements')
    required_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    class Meta:
        unique_together = ['opportunity', 'skill']

    def __str__(self):
        return f"{self.opportunity.title} requires {self.skill.skill_name}"
