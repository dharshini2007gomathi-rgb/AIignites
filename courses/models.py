"""
Learning resource and course recommendation models.
"""
from django.db import models
from skills.models import Skill


class Course(models.Model):
    """Courses mapped to skills for gap-filling recommendations."""

    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=300)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='courses')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    provider = models.CharField(max_length=200)
    link = models.URLField()
    duration = models.CharField(max_length=100, blank=True, null=True)
    is_free = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['skill', 'level']

    def __str__(self):
        return f"{self.course_name} ({self.level})"
