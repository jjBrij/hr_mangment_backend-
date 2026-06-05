# apps/performance/models.py
from django.db import models
from apps.accounts.models import User
from decimal import Decimal

class PerformanceTarget(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_targets')
    month = models.CharField(max_length=7)
    year = models.IntegerField()
    current_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    completed_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    user_entered_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    project_completion = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    task_efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    growth_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_targets'
        unique_together = ['employee', 'month']
    
    def save(self, *args, **kwargs):
        self.performance_score = (
        self.attendance * Decimal('0.4')
        + self.project_completion * Decimal('0.4')
        + self.task_efficiency * Decimal('0.2')
    )
        if self.previous_target > 0:
          self.growth_percentage = (
            (self.current_target - self.previous_target)
            / self.previous_target
        ) * Decimal('100')
        else:
         self.growth_percentage = Decimal('0')

        super().save(*args, **kwargs)


class DailyTarget(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_targets')
    date = models.DateField()
    completed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tasks = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_targets'
        unique_together = ['employee', 'date']


class PerformanceReview(models.Model):
    REVIEW_TYPES = (
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('project', 'Project Based'),
    )
    REVIEW_RATINGS = (
        (1, 'Poor'), (2, 'Below Average'), (3, 'Average'), (4, 'Good'), (5, 'Excellent'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    review_date = models.DateField()
    quarter = models.IntegerField(null=True, blank=True)
    year = models.IntegerField()
    quality_rating = models.IntegerField(choices=REVIEW_RATINGS)
    productivity_rating = models.IntegerField(choices=REVIEW_RATINGS)
    teamwork_rating = models.IntegerField(choices=REVIEW_RATINGS)
    communication_rating = models.IntegerField(choices=REVIEW_RATINGS)
    punctuality_rating = models.IntegerField(choices=REVIEW_RATINGS)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    strengths = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    reviewer_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_reviews'
    
    def save(self, *args, **kwargs):
        total = (self.quality_rating + self.productivity_rating + 
                self.teamwork_rating + self.communication_rating + self.punctuality_rating)
        self.average_rating = total / 5
        super().save(*args, **kwargs)