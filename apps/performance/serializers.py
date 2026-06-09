# apps/performance/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PerformanceTarget, DailyTarget, PerformanceReview

User = get_user_model()

class PerformanceTargetSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField()

    class Meta:
        model = PerformanceTarget
        fields = [
            'id',
            'employee_id',
            'month',
            'year',
            'current_target',
            'completed_target',
            'previous_target',
            'user_entered_target',
            'previous_pending',
            'attendance',
            'performance_score',
            'growth_percentage',
        ]

    def create(self, validated_data):
        employee_code = validated_data.pop('employee_id')

        employee = User.objects.get(
            employee_id=employee_code
        )

        validated_data['employee'] = employee

        return PerformanceTarget.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('employee_id', None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['employee_id'] = instance.employee.employee_id
        return data

class DailyTargetSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    # Adding write_only=True ensures this doesn't accidentally overwrite the representation later
    employee_id = serializers.CharField(write_only=True) 

    class Meta:
        model = DailyTarget
        fields = '__all__'
        # 💎 THIS is the absolute override. DRF will no longer validate the 'employee' field.
        read_only_fields = ('employee',) 

    def create(self, validated_data):
        employee_code = validated_data.pop('employee_id', None)

        if employee_code:
            employee = User.objects.get(employee_id=employee_code)
            validated_data['employee'] = employee
        else:
            validated_data['employee'] = self.context['request'].user

        return DailyTarget.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('employee_id', None)
        return super().update(instance, validated_data)

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['employee_id'] = instance.employee.employee_id
        return data

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