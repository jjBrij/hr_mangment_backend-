# apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'employee_id', 'phone'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match")
        return data


class ForgotUserIDSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email address")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email address")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users (Admin/HR only)"""
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = (
            'employee_id', 'email', 'first_name', 'last_name', 'phone',
            'date_of_birth', 'address', 'city', 'state', 'country', 'pincode',
            'profile_picture', 'confirm_password'
        )
    
    def validate_employee_id(self, value):
        """Validate employee ID is unique"""
        if User.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError(
                f"Employee ID '{value}' already exists. Please use a different ID."
            )
        return value
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        # Generate temporary password
        temp_password = User().generate_temporary_password()
        
        # Set username as email for simplicity
        validated_data['username'] = validated_data['email']
        
        # Set created_by from context (the logged-in user)
        validated_data['created_by'] = self.context['request'].user
        
        # Create user
        user = User.objects.create_user(**validated_data)
        user.set_password(temp_password)
        user.must_change_password = True
        user.save()
        
        # Send welcome email with credentials (optional)
        # self.send_welcome_email(user, temp_password)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'address', 'city', 'state', 'country', 'pincode', 'profile_picture'
        )


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users with role info"""
    full_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'employee_id', 'full_name', 'email', 'role', 'phone',
            'is_active', 'date_joined', 'created_by_name'
        )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else 'System'


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user view"""
    full_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('id', 'password', 'last_login', 'date_joined', 'created_at', 'updated_at')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else 'System'


class ChangeRoleSerializer(serializers.Serializer):
    """Serializer for changing user role (Admin only)"""
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_role(self, value):
        request = self.context.get('request')
        target_user = self.context.get('target_user')
        
        # Prevent demoting the last admin
        if target_user and target_user.role == 'admin' and value != 'admin':
            admin_count = User.objects.filter(role='admin', is_active=True).count()
            if admin_count <= 1:
                raise serializers.ValidationError(
                    "Cannot demote the last admin user. At least one admin must remain."
                )
        
        return value