# apps/employees/serializers.py
from rest_framework import serializers
from apps.accounts.models import User
from apps.employees.models import Employee
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class EmployeeCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'email', 'first_name', 'last_name',
            'department', 'position', 'joining_date', 'employment_type',
            'gender', 'blood_group', 'marital_status', 'nationality',
            'father_name', 'father_contact', 'mother_name', 'mother_contact',
            'spouse_name', 'spouse_contact', 'current_address', 'permanent_address',
            'emergency_contact_name', 'emergency_contact_relation', 'emergency_contact_number',
            'work_location', 'reporting_manager', 'basic_salary', 'current_salary',
            'previous_company', 'previous_salary', 'bank_name', 'account_number',
            'ifsc_code', 'bank_passbook', 'aadhar_card', 'pan_card', 'passport_photo', 'resume'
        ]
        read_only_fields = ['employee_id']
    
    def create(self, validated_data):
        # Extract user fields
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        
        # Generate temporary password
        temp_password = User().generate_temporary_password()
        
        # Create user account
        user = User.objects.create(
            username=email,  # Use email as username for simplicity
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='employee',
            must_change_password=True,
            is_active=True
        )
        user.set_password(temp_password)
        user.save()
        
        # Get created_by from context (admin/hr_manager who is creating)
        created_by = self.context.get('created_by')
        if created_by:
            user.created_by = created_by
            user.save()
        
        # Create employee profile
        employee = Employee.objects.create(
            user=user,
            **validated_data
        )
        
        # Send credentials email
        self.send_credentials_email(employee, temp_password)
        
        return employee
    
    def send_credentials_email(self, employee, temp_password):
        """Send email with login credentials to employee"""
        subject = 'Welcome to HRMS - Your Login Credentials'
        
        context = {
            'employee_name': employee.user.get_full_name(),
            'employee_id': employee.employee_id,
            'temp_password': temp_password,
            'login_url': settings.FRONTEND_URL,
            'company_name': 'HRMS',
            'support_email': settings.DEFAULT_FROM_EMAIL
        }
        
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = f"""
        Dear {employee.user.get_full_name()},
        
        Welcome to HRMS! Your account has been created successfully.
        
        Your Login Credentials:
        Employee ID: {employee.employee_id}
        Temporary Password: {temp_password}
        
        Please login using the link below and change your password immediately.
        
        Login URL: {settings.FRONTEND_URL}
        
        For security reasons, you will be required to change your password on first login.
        
        If you have any questions, please contact HR department.
        
        Best regards,
        HRMS Team
        """
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.user.email],
            fail_silently=False,
            html_message=html_message
        )

class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['employee_id', 'user']

class EmployeeListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'name', 'email', 'department', 'position', 
                  'joining_date', 'status', 'employment_type']
    
    def get_name(self, obj):
        return obj.user.get_full_name()
    
    def get_email(self, obj):
        return obj.user.email

class EmployeeDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    date_of_birth = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def get_name(self, obj):
        return obj.user.get_full_name()
    
    def get_email(self, obj):
        return obj.user.email
    
    def get_phone(self, obj):
        return obj.user.phone
    
    def get_date_of_birth(self, obj):
        return obj.user.date_of_birth   