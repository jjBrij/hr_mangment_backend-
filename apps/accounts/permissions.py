# apps/accounts/permissions.py
from rest_framework import permissions

class IsAdminOrHRManager(permissions.BasePermission):
    """Allow access only to Admin or HR Manager"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'hr_manager']


class IsAdmin(permissions.BasePermission):
    """Allow access only to Admin"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'


class IsEmployee(permissions.BasePermission):
    """Allow access only to Employee"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.role == 'employee'