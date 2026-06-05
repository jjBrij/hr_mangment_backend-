
# apps/performance/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from .models import PerformanceTarget, DailyTarget, PerformanceReview
from .serializers import (
    PerformanceTargetSerializer, DailyTargetSerializer, PerformanceReviewSerializer
)
from apps.accounts.permissions import IsAdminOrHRManager


class PerformanceTargetViewSet(viewsets.ModelViewSet):
    queryset = PerformanceTarget.objects.all()
    serializer_class = PerformanceTargetSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrHRManager()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get performance statistics for dashboard"""
        month = request.query_params.get('month', datetime.now().strftime('%Y-%m'))
        targets = PerformanceTarget.objects.filter(month=month)
        
        total_employees = targets.count()
        avg_performance = targets.aggregate(Avg('performance_score'))['performance_score__avg'] or 0
        highest_attendance = targets.aggregate(Avg('attendance'))['attendance__avg'] or 0
        
        # Calculate average completion rate
        total_completion = 0
        for target in targets:
            if target.current_target > 0:
                total_completion += (target.completed_target / target.current_target) * 100
        avg_completion = total_completion / total_employees if total_employees > 0 else 0
        
        # Top 3 performers
        top_performers = targets.order_by('-performance_score')[:3]
        top_list = []
        for performer in top_performers:
            top_list.append({
                'employeeName': performer.employee.get_full_name(),
                'employeeId': performer.employee.employee_id,
                'department': self.get_department(performer.employee),
                'performanceScore': performer.performance_score
            })
        
        return Response({
            'totalEmployees': total_employees,
            'averagePerformance': round(avg_performance, 2),
            'highestAttendance': round(highest_attendance, 2),
            'targetCompletion': round(avg_completion, 2),
            'topEmployees': top_list
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get performance trends for charts"""
        months = int(request.query_params.get('months', 6))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        trends = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month = current_date.strftime('%Y-%m')
            targets = PerformanceTarget.objects.filter(month=month)
            
            avg_score = targets.aggregate(Avg('performance_score'))['performance_score__avg'] or 0
            avg_attendance = targets.aggregate(Avg('attendance'))['attendance__avg'] or 0
            
            total_completion = 0
            for target in targets:
                if target.current_target > 0:
                    total_completion += (target.completed_target / target.current_target) * 100
            avg_completion = total_completion / targets.count() if targets.count() > 0 else 0
            
            trends.append({
                'month': current_date.strftime('%b %Y'),
                'score': round(avg_score, 1),
                'attendance': round(avg_attendance, 1),
                'completionRate': round(avg_completion, 1)
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return Response(trends)
    
    def get_department(self, employee):
        try:
            return employee.employee_profile.department
        except:
            return ''


class DailyTargetViewSet(viewsets.ModelViewSet):
    queryset = DailyTarget.objects.all()
    serializer_class = DailyTargetSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'employee':
            return DailyTarget.objects.filter(employee=user)
        return DailyTarget.objects.all()
    
    @action(detail=False, methods=['get'])
    def my_targets(self, request):
        """Get daily targets for current logged-in employee"""
        user = request.user
        month = request.query_params.get('month', datetime.now().strftime('%Y-%m'))
        
        targets = DailyTarget.objects.filter(
            employee=user,
            date__year=int(month.split('-')[0]),
            date__month=int(month.split('-')[1])
        ).order_by('date')
        
        serializer = self.get_serializer(targets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create daily targets for a month"""
        employee_id = request.data.get('employeeId')
        month = request.data.get('month')
        
        from apps.accounts.models import User
        employee = User.objects.get(employee_id=employee_id)
        
        year, month_num = map(int, month.split('-'))
        _, last_day = monthrange(year, month_num)
        
        created_count = 0
        for day in range(1, last_day + 1):
            date = datetime(year, month_num, day).date()
            _, created = DailyTarget.objects.get_or_create(
                employee=employee,
                date=date,
                defaults={'completed_amount': 0, 'tasks': []}
            )
            if created:
                created_count += 1
        
        return Response({'message': f'Created {created_count} daily targets'})
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Update performance target total completed amount
        month = instance.date.strftime('%Y-%m')
        total_completed = DailyTarget.objects.filter(
            employee=instance.employee,
            date__year=instance.date.year,
            date__month=instance.date.month
        ).aggregate(Sum('completed_amount'))['completed_amount__sum'] or 0
        
        performance_target = PerformanceTarget.objects.filter(
            employee=instance.employee,
            month=month
        ).first()
        
        if performance_target:
            performance_target.completed_target = total_completed
            performance_target.save()


class PerformanceReviewViewSet(viewsets.ModelViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrHRManager()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)