# apps/employees/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter, DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from apps.employees.models import Employee
from apps.employees.serializers import (
    EmployeeCreateSerializer, EmployeeUpdateSerializer,
    EmployeeListSerializer, EmployeeDetailSerializer
)
from apps.accounts.permissions import IsAdminOrHRManager

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'status', 'employment_type']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['created_at', 'joining_date', 'employee_id']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminOrHRManager]
        else:
            permission_classes = [IsAuthenticated]
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
        # Pass the current user as created_by
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resend_credentials(self, request, pk=None):
        """Resend login credentials to employee"""
        employee = self.get_object()
        
        # Generate new temporary password
        temp_password = employee.user.generate_temporary_password()
        employee.user.set_password(temp_password)
        employee.user.must_change_password = True
        employee.user.save()
        
        # Send email with new credentials
        from apps.employees.serializers import EmployeeCreateSerializer
        serializer = EmployeeCreateSerializer()
        serializer.send_credentials_email(employee, temp_password)
        
        return Response({
            'message': 'Credentials resent successfully',
            'employee_id': employee.employee_id
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current logged-in employee profile"""
        try:
            employee = Employee.objects.get(user=request.user)
            serializer = EmployeeDetailSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee profile not found'}, status=404)