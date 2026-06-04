# apps/accounts/permissions.py
from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Allows access only to admin users"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrHRManager(permissions.BasePermission):
    """Allows access to admin and HR managers"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'hr_manager']
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'hr_manager']


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allows access to the owner of the object or admin"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Users can access their own data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'employee'):
            return obj.employee == request.user
        else:
            return obj == request.user


class EmployeeReadOnly(permissions.BasePermission):
    """Employees can only read data, cannot modify"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # GET requests are allowed for employees
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST, PUT, DELETE only for admin/HR
        return request.user.role in ['admin', 'hr_manager']


class CustomDjangoPermission(permissions.DjangoModelPermissions):
    """Use Django's built-in permissions"""
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }