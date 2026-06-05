# apps/employees/serializers.py - Complete fixed version
from rest_framework import serializers
from apps.accounts.models import User
from .models import Employee

class EmployeeCreateSerializer(serializers.Serializer):
    """Serializer for creating employee from frontend"""
    # Basic Information
    fullName = serializers.CharField(write_only=True)
    employeeId = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    phone = serializers.CharField()
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True)
    bloodGroup = serializers.CharField(required=False, allow_null=True)
    maritalStatus = serializers.CharField(required=False, allow_null=True)
    nationality = serializers.CharField(required=False, default='Indian')
    
    # Family Information
    fatherName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fatherContact = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    motherName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    motherContact = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    spouseName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    spouseContact = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Address
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    permanentAddress = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Emergency Contact
    emergencyContactName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emergencyContactRelation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emergencyContactNumber = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Job Information
    department = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)  # Keep for frontend
    workLocation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    employmentType = serializers.CharField(required=False, default='Full-time')
    joiningDate = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField(required=False, default='Active')
    
    # Salary
    basicSalary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    currentSalary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    previousCompany = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    previousSalary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    # Bank Information
    bankName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    accountNumber = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ifscCode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_employeeId(self, value):
        """Validate employee ID is unique"""
        if Employee.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError(f"Employee ID {value} already exists")
        return value
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        # Extract user fields
        full_name = validated_data.pop('fullName', '')
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        email = validated_data.pop('email')
        employee_id = validated_data.pop('employeeId')
        phone = validated_data.pop('phone', '')
        date_of_birth = validated_data.pop('dateOfBirth', None)
        
        # Get position from designation field (frontend sends designation)
        position = validated_data.pop('designation', '')
        
        # Create User Account
        temp_password = User().generate_temporary_password()
        
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            employee_id=employee_id,
            role='employee',
            phone=phone,
            date_of_birth=date_of_birth,
            must_change_password=True,
            is_active=True
        )
        user.set_password(temp_password)
        user.save()
        
        # Create Employee Profile
        employee = Employee.objects.create(
            user=user,
            employee_id=employee_id,
            email=email,
            phone=phone,
            father_name=validated_data.get('fatherName', ''),
            father_contact=validated_data.get('fatherContact', ''),
            mother_name=validated_data.get('motherName', ''),
            mother_contact=validated_data.get('motherContact', ''),
            spouse_name=validated_data.get('spouseName', ''),
            spouse_contact=validated_data.get('spouseContact', ''),
            current_address=validated_data.get('address', ''),
            permanent_address=validated_data.get('permanentAddress', ''),
            emergency_contact_name=validated_data.get('emergencyContactName', ''),
            emergency_contact_relation=validated_data.get('emergencyContactRelation', ''),
            emergency_contact_number=validated_data.get('emergencyContactNumber', ''),
            department=validated_data.get('department', ''),
            position=position,  # Use designation as position
            work_location=validated_data.get('workLocation', ''),
            employment_type=validated_data.get('employmentType', 'Full-time'),
            joining_date=validated_data.get('joiningDate'),
            status=validated_data.get('status', 'Active'),
            gender=validated_data.get('gender', ''),
            blood_group=validated_data.get('bloodGroup', ''),
            marital_status=validated_data.get('maritalStatus', ''),
            nationality=validated_data.get('nationality', 'Indian'),
            basic_salary=validated_data.get('basicSalary', 0),
            current_salary=validated_data.get('currentSalary', 0),
            previous_company=validated_data.get('previousCompany', ''),
            previous_salary=validated_data.get('previousSalary', None),
            bank_name=validated_data.get('bankName', ''),
            account_number=validated_data.get('accountNumber', ''),
            ifsc_code=validated_data.get('ifscCode', ''),
        )
        
        # Send email with credentials
        self.send_credentials_email(employee, temp_password)
        
        return employee
    
    def to_representation(self, instance):
        """Return employee data after creation"""
        return {
            'id': instance.id,
            'employee_id': instance.employee_id,
            'name': instance.user.get_full_name(),
            'email': instance.email,
            'department': instance.department,
            'position': instance.position,
            'status': instance.status,
            'message': 'Employee created successfully'
        }
    
    def send_credentials_email(self, employee, temp_password):
        """Send welcome email to new employee"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Welcome to HRMS - Your Account Credentials'
        message = f"""
        Dear {employee.user.get_full_name()},
        
        Your account has been created successfully in the HRMS system.
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        YOUR LOGIN CREDENTIALS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        User ID: {employee.employee_id}
        Password: {temp_password}
        Login URL: {settings.FRONTEND_URL}
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        IMPORTANT INSTRUCTIONS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        1. Use the above User ID and Password to login
        2. You will be required to change your password on first login
        3. Do not share your credentials with anyone
        
        Best regards,
        HRMS Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [employee.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email could not be sent: {str(e)}")


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for listing employees"""
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
    """Serializer for employee details"""
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


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee"""
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email')
    phone = serializers.CharField(source='user.phone')
    date_of_birth = serializers.DateField(source='user.date_of_birth')
    
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['employee_id', 'user']
    
    def update(self, instance, validated_data):
        # Update User fields
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            if 'email' in user_data:
                user.email = user_data['email']
                user.username = user_data['email']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            if 'date_of_birth' in user_data:
                user.date_of_birth = user_data['date_of_birth']
            user.save()
        
        # Update Employee fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance