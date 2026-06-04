# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
import secrets
import string

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('hr_manager', 'HR Manager'),
        ('employee', 'Employee'),
    )
    
    # Auto-set role based on who created the user
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    employee_id = models.CharField(max_length=20, unique=True, db_index=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)
    
    # Track who created this user
    created_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        permissions = [
            ("can_view_all_employees", "Can view all employees"),
            ("can_edit_all_employees", "Can edit all employees"),
            ("can_delete_employees", "Can delete employees"),
            ("can_view_payroll", "Can view payroll"),
            ("can_process_payroll", "Can process payroll"),
            ("can_manage_leave", "Can manage leave requests"),
            ("can_view_reports", "Can view reports"),
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"
    
    def clean(self):
        super().clean()
        # Validate employee_id format
        if self.employee_id and not re.match(r'^[A-Za-z0-9]{4,20}$', self.employee_id):
            raise ValidationError({'employee_id': 'Employee ID must be 4-20 alphanumeric characters'})
    
    def save(self, *args, **kwargs):
        # Auto-assign role based on creator if not set
        if not self.pk and not self.role:
            if self.created_by:
                # If created by admin or hr_manager, new user becomes employee
                if self.created_by.role in ['admin', 'hr_manager']:
                    self.role = 'employee'
                else:
                    self.role = 'employee'  # Default
            else:
                # Superuser creation via command line
                if self.is_superuser:
                    self.role = 'admin'
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def generate_temporary_password(self):
        """Generate a random temporary password"""
        alphabet = string.ascii_letters + string.digits + '!@#$%'
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        return password


class PasswordResetToken(models.Model):
    """Model for storing password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.employee_id} - {'Valid' if self.is_valid() else 'Expired'}"


class LoginHistory(models.Model):
    """Model for tracking user login history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_history'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.login_time}"


class UserRoleHistory(models.Model):
    """Track role changes for audit purposes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_history')
    old_role = models.CharField(max_length=20)
    new_role = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='role_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_role_history'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.user.employee_id}: {self.old_role} -> {self.new_role} by {self.changed_by.employee_id if self.changed_by else 'System'}"