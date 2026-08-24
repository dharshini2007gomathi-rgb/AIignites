"""
Application tracking and internship management models.
"""
from django.db import models
from students.models import Student
from opportunities.models import Opportunity


class Application(models.Model):
    """Student applications to opportunities."""

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview', 'Interview'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
    ]

    application_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'opportunity']
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.student.name} -> {self.opportunity.title} ({self.status})"


class Internship(models.Model):
    """Active internship tracking after selection."""

    STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Terminated', 'Terminated'),
    ]

    internship_id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='internship')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    mentor_name = models.CharField(max_length=200)
    mentor_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ongoing')
    tasks_completed = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=10)
    final_evaluation = models.TextField(blank=True, null=True)
    certificate_issued = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Internship #{self.internship_id} - {self.application.student.name}"


class InternshipProgress(models.Model):
    """Weekly progress logs during internship."""

    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='progress_logs')
    week_number = models.IntegerField()
    tasks_done = models.TextField()
    mentor_feedback = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_number']

    def __str__(self):
        return f"Week {self.week_number} - Internship #{self.internship.internship_id}"
