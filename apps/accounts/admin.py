# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from hrms_backend import settings
from .models import User, LoginHistory, PasswordResetToken,UserRoleHistory

class UserAdmin(BaseUserAdmin):
    list_display = ('employee_id', 'full_name', 'email', 'role', 'department', 'is_active', 'must_change_password')
    list_filter = ('role', 'is_active', 'department', 'must_change_password')
    search_fields = ('employee_id', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password', 'employee_id')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_picture', 'date_of_birth')
        }),
        ('Employment Information', {
            'fields': ('role', 'department', 'position', 'joining_date')
        }),
        ('Address Information', {
            'fields': ['address']
        }),
        ('Account Status', {
            'fields': ('is_active', 'must_change_password', 'created_by')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Create New User', {
            'fields': ('employee_id', 'email', 'first_name', 'last_name', 'role', 'department', 'position', 'password1', 'password2')
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Name'
    
    def save_model(self, request, obj, form, change):
        is_new = not change
        if is_new:  # If creating new user
            obj.created_by = request.user
            obj.must_change_password = True
        super().save_model(request, obj, form, change)
        if is_new:
            self.send_welcome_email(request, obj, form.cleaned_data.get('password1', 'Temporary@123'))
    
    actions = ['make_active', 'make_inactive', 'reset_user_password']
    def send_welcome_email(self, request, user, temp_password):
        """Send welcome email to new user"""
        subject = f'Welcome to HRMS - Your Account Credentials'
        
        # Determine login URL based on role
        if user.role in ['admin', 'hr_manager']:
            login_url = f"{settings.FRONTEND_URL}/admin/login"
        else:
            login_url = f"{settings.FRONTEND_URL}/employee/login"
        
        message = f"""
        Dear {user.get_full_name()},
        
        Welcome to HRMS! Your account has been created successfully.
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        YOUR LOGIN CREDENTIALS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        User ID: {user.employee_id}
        Password: {temp_password}
        Role: {user.role.upper()}
        
        Login URL: {login_url}
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        IMPORTANT INSTRUCTIONS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        1. Use the above User ID and Password to login
        2. You will be required to change your password on first login
        3. Do not share your credentials with anyone
        4. For security, please use a strong password
        
        If you have any questions, please contact your HR department.
        
        Best regards,
        HRMS Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            self.message_user(request, f"Welcome email sent to {user.email}")
        except Exception as e:
            self.message_user(request, f"Warning: Email could not be sent to {user.email}. Error: {str(e)}")
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.")
    make_active.short_description = "Activate selected users"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")
    make_inactive.short_description = "Deactivate selected users"
    
    def reset_user_password(self, request, queryset):
        for user in queryset:
            temp_password = User().generate_temporary_password()
            user.set_password(temp_password)
            user.must_change_password = True
            user.save()
        self.message_user(request, f"Password reset for {queryset.count()} user(s).")
    reset_user_password.short_description = "Reset password for selected users"

# Register the User model with the custom admin
admin.site.register(User, UserAdmin)

# Optional: Register other models if they exist
try:
    admin.site.register(LoginHistory)
    admin.site.register(PasswordResetToken)
    admin.site.register(UserRoleHistory)
except:
    pass

# Customize admin site headers
admin.site.site_header = 'HRMS Administration'
admin.site.site_title = 'HRMS Admin Panel'
admin.site.index_title = 'Welcome to HRMS Admin Dashboard'