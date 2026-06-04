# apps/accounts/views.py
from rest_framework import status, generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import secrets
from .models import User, PasswordResetToken, LoginHistory, UserRoleHistory
from .serializers import (
    UserSerializer, LoginSerializer, ChangePasswordSerializer,
    ForgotUserIDSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    UserCreateSerializer, UserUpdateSerializer, UserListSerializer,
    UserDetailSerializer, ChangeRoleSerializer
)
from .permissions import IsAdmin, IsAdminOrHRManager, IsOwnerOrAdmin

# ============ AUTHENTICATION VIEWS ============

class RegisterView(generics.CreateAPIView):
    """Public registration - Only for testing, should be disabled in production"""
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Try to find user by employee_id or email or username
        user = None
        if User.objects.filter(employee_id=username).exists():
            user = User.objects.get(employee_id=username)
        elif User.objects.filter(email=username).exists():
            user = User.objects.get(email=username)
        elif User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate
        authenticated_user = authenticate(username=user.username, password=password)
        
        if not authenticated_user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({'error': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)
        
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
                'is_active': user.is_active,
            },
            'must_change_password': must_change_password
        }
        
        return Response(response_data)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Verify current password
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save()
        
        # Generate new tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Password changed successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })


class ForgotUserIDView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotUserIDSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Send email with employee ID
        subject = 'Your Employee ID - HRMS'
        message = f"""
        Dear {user.get_full_name()},
        
        Your Employee ID is: {user.employee_id}
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        HRMS Team
        """
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        
        return Response({'message': 'Employee ID has been sent to your registered email address'})


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
        
        # Send reset link email
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = 'Password Reset Request - HRMS'
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
        
        return Response({'message': 'Password reset link has been sent to your registered email address'})


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
                return Response({'error': 'Reset token has expired or been used'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = reset_token.user
            user.set_password(new_password)
            user.must_change_password = False
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            return Response({'message': 'Password reset successfully'})
            
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid reset token'}, status=status.HTTP_400_BAD_REQUEST)


class RecoverAccountInfoView(generics.GenericAPIView):
    """Handle case when user forgets both Employee ID and Email"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        return Response({
            'message': 'Please contact your HR department or system administrator to verify your identity and recover your account.',
            'support_contact': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
        })


class GetCurrentUserView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ============ USER MANAGEMENT VIEWSET (Admin/HR only) ============

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management with role-based permissions.
    Only Admin and HR Managers can access these endpoints.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
    ordering_fields = ['employee_id', 'date_joined', 'first_name']
    ordering = ['employee_id']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            # Admin/HR can create users
            permission_classes = [IsAuthenticated, IsAdminOrHRManager]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only admin can delete, owners can update their own profile partially
            if self.action == 'destroy':
                permission_classes = [IsAuthenticated, IsAdmin]
            else:
                permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'list':
            # Admin/HR can list all users
            permission_classes = [IsAuthenticated, IsAdminOrHRManager]
        elif self.action == 'me':
            # Anyone can access their own profile
            permission_classes = [IsAuthenticated]
        elif self.action in ['change_role', 'activate', 'deactivate', 'bulk_create']:
            # Only admin can perform these actions
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        else:
            return UserDetailSerializer
    
    def perform_create(self, serializer):
        """Create user - role is automatically set to employee"""
        serializer.save()
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user profile"""
        user = request.user
        
        if request.method == 'GET':
            serializer = UserDetailSerializer(user, context={'request': request})
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'Profile updated successfully'})
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Change user role (Admin only)"""
        user = self.get_object()
        serializer = ChangeRoleSerializer(
            data=request.data,
            context={'request': request, 'target_user': user}
        )
        serializer.is_valid(raise_exception=True)
        
        old_role = user.role
        new_role = serializer.validated_data['role']
        
        if old_role == new_role:
            return Response({'message': 'Role is already set to this value'})
        
        # Change role
        user.role = new_role
        user.save()
        
        # Log role change
        UserRoleHistory.objects.create(
            user=user,
            old_role=old_role,
            new_role=new_role,
            changed_by=request.user,
            reason=serializer.validated_data.get('reason', '')
        )
        
        return Response({
            'message': f'Role changed from {old_role} to {new_role} successfully',
            'user_id': user.id,
            'employee_id': user.employee_id,
            'new_role': new_role
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create users (Admin only)"""
        users_data = request.data.get('users', [])
        created_users = []
        errors = []
        
        for user_data in users_data:
            serializer = UserCreateSerializer(
                data=user_data,
                context={'request': request}
            )
            if serializer.is_valid():
                user = serializer.save()
                created_users.append({
                    'employee_id': user.employee_id,
                    'email': user.email,
                    'name': user.get_full_name()
                })
            else:
                errors.append({
                    'data': user_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created_count': len(created_users),
            'created_users': created_users,
            'errors': errors,
            'error_count': len(errors)
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account (Admin only)"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': f'User {user.employee_id} activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account (Admin only)"""
        user = self.get_object()
        
        # Prevent deactivating the last admin
        if user.role == 'admin' and User.objects.filter(role='admin', is_active=True).count() <= 1:
            return Response(
                {'error': 'Cannot deactivate the last admin user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.save()
        return Response({'message': f'User {user.employee_id} deactivated successfully'})