from django.urls import path
from . import views

urlpatterns = [
    # Authentication (Public)
    path('login/', views.LoginView.as_view(), name='login'),
    path('forgot-userid/', views.ForgotUserIDView.as_view(), name='forgot-userid'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # User Profile (Authenticated)
    path('me/', views.GetCurrentUserView.as_view(), name='current-user'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update-profile'),

    # Employee Management (HR/Admin only)
    path('employees/create/', views.CreateEmployeeView.as_view(), name='create-employee'),
    path('employees/list/', views.ListEmployeesView.as_view(), name='list-employees'),
]