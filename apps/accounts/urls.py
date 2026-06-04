# apps/accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSet
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    # Authentication URLs (public)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('forgot-userid/', views.ForgotUserIDView.as_view(), name='forgot-userid'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('recover-account/', views.RecoverAccountInfoView.as_view(), name='recover-account'),
    path('me/', views.GetCurrentUserView.as_view(), name='current-user'),
    
    # User Management URLs (protected - Admin/HR only)
    path('', include(router.urls)),
]
