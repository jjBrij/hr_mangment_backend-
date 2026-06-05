# apps/performance/admin.py
from django.contrib import admin
from .models import PerformanceTarget, DailyTarget, PerformanceReview

@admin.register(PerformanceTarget)
class PerformanceTargetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'current_target', 'completed_target', 'performance_score']
    list_filter = ['month', 'year']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']

@admin.register(DailyTarget)
class DailyTargetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'completed_amount', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'review_type', 'review_date', 'average_rating']
    list_filter = ['review_type', 'year']
    search_fields = ['employee__first_name', 'employee__last_name']