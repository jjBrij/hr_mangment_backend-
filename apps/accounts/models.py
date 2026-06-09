# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager  # ← BaseUserManager here


from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string


class UserManager(BaseUserManager):
    def create_user(self, employee_id, email, password=None, **extra_fields):
        if not employee_id:
            raise ValueError('Employee ID is required')
        email = self.normalize_email(email)
        user = self.model(employee_id=employee_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('must_change_password', False)
        return self.create_user(employee_id, email, password, **extra_fields)        

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('hr_manager', 'HR Manager'),
        ('employee', 'Employee'),
    )

    # Override username — remove unique constraint, make it optional
    username = models.CharField(max_length=150, blank=True, default='')
    objects = UserManager()   

    # Basic Information
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    # Employment Information
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    # Account Status
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)

    # Tracking
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use employee_id as the login field instead of username
    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email']  # asked by createsuperuser

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def generate_temporary_password(self):
        alphabet = string.ascii_letters + string.digits + '!@#$%'
        return ''.join(secrets.choice(alphabet) for _ in range(12))

    def send_welcome_email(self, temp_password):
        subject = 'Welcome to HRMS - Your Account Credentials'
        message = f"""
Dear {self.get_full_name()},

Your account has been created in the HRMS system.

Login Credentials:
─────────────────
User ID: {self.employee_id}
Temporary Password: {temp_password}
Login URL: {settings.FRONTEND_URL}

⚠️ Important: You will be required to change your password on first login.

For security reasons, please do not share your credentials with anyone.

Best regards,
HRMS Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    class Meta:
        db_table = 'password_reset_tokens'


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_history'
        ordering = ['-login_time']


class UserRoleHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_history')
    old_role = models.CharField(max_length=20)
    new_role = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='role_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'user_role_history'

