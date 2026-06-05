# apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'employee_id', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'phone', 'department', 'position', 'joining_date',
                  'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined')
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for HR/Admin to create employees"""
    
    class Meta:
        model = User
        fields = ('employee_id', 'email', 'first_name', 'last_name', 'phone',
                  'department', 'position', 'joining_date', 'date_of_birth', 'address')
    
    def validate_employee_id(self, value):
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError(f"Employee ID '{value}' already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        # Generate temporary password
        temp_password = User().generate_temporary_password()
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['employee_id'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            employee_id=validated_data['employee_id'],
            phone=validated_data.get('phone', ''),
            department=validated_data.get('department', ''),
            position=validated_data.get('position', ''),
            joining_date=validated_data.get('joining_date'),
            date_of_birth=validated_data.get('date_of_birth'),
            address=validated_data.get('address', ''),
            role='employee',
            must_change_password=True
        )
        user.set_password(temp_password)
        user.save()
        
        # Set created_by from context
        if self.context.get('request'):
            user.created_by = self.context['request'].user
            user.save()
        
        # Send welcome email
        user.send_welcome_email(temp_password)
        
        return user


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user_id = data.get('user_id')
        password = data.get('password')
        
        # Find user by employee_id or email
        user = None
        if User.objects.filter(employee_id=user_id).exists():
            user = User.objects.get(employee_id=user_id)
        elif User.objects.filter(email=user_id).exists():
            user = User.objects.get(email=user_id)
        
        if not user:
            raise serializers.ValidationError("Invalid User ID or Password")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid User ID or Password")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled. Contact HR.")
        
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match")
        return data


class ForgotUserIDSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data