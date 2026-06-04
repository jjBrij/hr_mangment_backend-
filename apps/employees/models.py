# apps/employees/models.py
from django.db import models
from apps.accounts.models import User

class Employee(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    )
    
    MARITAL_STATUS = (
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    )
    
    DEPARTMENT_CHOICES = (
        ('Engineering', 'Engineering'),
        ('HR', 'Human Resources'),
        ('Finance', 'Finance'),
        ('Marketing', 'Marketing'),
        ('Sales', 'Sales'),
        ('Operations', 'Operations'),
    )
    
    EMPLOYMENT_TYPE = (
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
    )
    
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
        ('Terminated', 'Terminated'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    position = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='Full-time')
    joining_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    # Personal Information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    
    # Family Information
    father_name = models.CharField(max_length=100, blank=True)
    father_contact = models.CharField(max_length=15, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    mother_contact = models.CharField(max_length=15, blank=True)
    spouse_name = models.CharField(max_length=100, blank=True)
    spouse_contact = models.CharField(max_length=15, blank=True)
    
    # Address
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    
    # Work Information
    work_location = models.CharField(max_length=100, blank=True)
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    previous_company = models.CharField(max_length=100, blank=True)
    previous_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Bank Information
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    bank_passbook = models.FileField(upload_to='documents/bank/', blank=True, null=True)
    
    # Documents
    aadhar_card = models.FileField(upload_to='documents/aadhar/', blank=True, null=True)
    pan_card = models.FileField(upload_to='documents/pan/', blank=True, null=True)
    passport_photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    resume = models.FileField(upload_to='documents/resume/', blank=True, null=True)
    
    # Educational Documents
    tenth_marksheet = models.FileField(upload_to='documents/education/', blank=True, null=True)
    twelfth_marksheet = models.FileField(upload_to='documents/education/', blank=True, null=True)
    graduation_marksheet = models.FileField(upload_to='documents/education/', blank=True, null=True)
    post_graduation_marksheet = models.FileField(upload_to='documents/education/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employee.objects.order_by('-id').first()
            if last_employee:
                last_id = int(last_employee.employee_id[3:])
                self.employee_id = f"EMP{str(last_id + 1).zfill(3)}"
            else:
                self.employee_id = "EMP001"
        super().save(*args, **kwargs)