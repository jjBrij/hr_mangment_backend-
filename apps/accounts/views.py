# apps/accounts/views.py
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets
from .models import User, PasswordResetToken, LoginHistory
from .serializers import (
    UserSerializer, EmployeeCreateSerializer, LoginSerializer,
    ChangePasswordSerializer, ForgotUserIDSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from .permissions import IsAdminOrHRManager

# ============ AUTHENTICATION VIEWS ============

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Check if password needs to be changed
        must_change_password = user.must_change_password
        
        # Create JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Log login history
        LoginHistory.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'employee_id': user.employee_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'department': user.department,
                'position': user.position
            },
            'must_change_password': must_change_password
        }
        
        return Response(response_data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            return Response(
                {'error': 'All password fields are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new passwords match
        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check password length
        if len(new_password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current password
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.must_change_password = False
        user.save()
        
        # Generate new tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Password changed successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })

class ForgotUserIDView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotUserIDSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        subject = 'Your User ID - HRMS'
        message = f"""
        Dear {user.get_full_name()},
        
        Your User ID is: {user.employee_id}
        
        Use this ID to login to your HRMS account.
        
        Best regards,
        HRMS Team
        """
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        
        return Response({'message': 'User ID has been sent to your email'})


class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=1)
        
        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        reset_link = f"{settings.BACKEND_URL}/api/auth/reset-password?token={token}"
        subject = 'Password Reset - HRMS'
        message = f"""
        Dear {user.get_full_name()},
        
        Click the link below to reset your password:
        {reset_link}
        
        This link expires in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        HRMS Team
        """
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        
        return Response({'message': 'Password reset link has been sent to your email'})


class ResetPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid():
                return Response({'error': 'Reset link has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = reset_token.user
            user.set_password(new_password)
            user.must_change_password = False
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            return Response({'message': 'Password reset successfully'})
            
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid reset token'}, status=status.HTTP_400_BAD_REQUEST)


# ============ EMPLOYEE MANAGEMENT (HR/ADMIN ONLY) ============

class CreateEmployeeView(generics.CreateAPIView):
    """HR/Admin can create employee accounts"""
    permission_classes = [IsAuthenticated, IsAdminOrHRManager]
    serializer_class = EmployeeCreateSerializer
    
    def perform_create(self, serializer):
        serializer.save()


class ListEmployeesView(generics.ListAPIView):
    """HR/Admin can list all employees"""
    permission_classes = [IsAuthenticated, IsAdminOrHRManager]
    serializer_class = UserSerializer
    queryset = User.objects.filter(role='employee')


class GetCurrentUserView(generics.RetrieveAPIView):
    """Get current logged-in user details"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class UpdateProfileView(generics.UpdateAPIView):
    """Update own profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user