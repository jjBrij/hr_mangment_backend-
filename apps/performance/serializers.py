# apps/performance/serializers.py
from rest_framework import serializers
from .models import PerformanceTarget, DailyTarget, PerformanceReview

class PerformanceTargetSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceTarget
        fields = '__all__'
        read_only_fields = ('id', 'performance_score', 'growth_percentage', 'created_at', 'updated_at')
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_department(self, obj):
        try:
            return obj.employee.employee_profile.department
        except:
            return ''


class DailyTargetSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyTarget
        fields = '__all__'
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceReview
        fields = '__all__'
        read_only_fields = ('id', 'average_rating', 'created_at', 'updated_at')
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() if obj.reviewer else ''