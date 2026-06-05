# apps/employees/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Employee
from .serializers import (
    EmployeeCreateSerializer, EmployeeListSerializer,
    EmployeeDetailSerializer, EmployeeUpdateSerializer
)
from apps.accounts.permissions import IsAdminOrHRManager

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'status', 'employment_type']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['joining_date', 'employee_id']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
        elif self.action == 'list':
            permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        elif self.action == 'list':
            return EmployeeListSerializer
        else:
            return EmployeeDetailSerializer
    
    def perform_create(self, serializer):
        """Create employee with current user as creator"""
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get employee documents"""
        employee = self.get_object()
        documents = {
            'aadhar_card': employee.aadhar_card.url if employee.aadhar_card else None,
            'pan_card': employee.pan_card.url if employee.pan_card else None,
            'passport_photo': employee.passport_photo.url if employee.passport_photo else None,
            'resume': employee.resume.url if employee.resume else None,
            'bank_passbook': employee.bank_passbook.url if employee.bank_passbook else None,
        }
        return Response(documents)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current logged-in employee profile"""
        try:
            employee = Employee.objects.get(user=request.user)
            serializer = EmployeeDetailSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee profile not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get employee statistics for dashboard"""
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status='Active').count()
        on_leave = Employee.objects.filter(status='On Leave').count()
        
        # Department wise count
        departments = {}
        for dept in Employee.objects.values_list('department', flat=True).distinct():
            if dept:
                departments[dept] = Employee.objects.filter(department=dept).count()
        
        return Response({
            'total': total_employees,
            'active': active_employees,
            'on_leave': on_leave,
            'departments': departments
        })