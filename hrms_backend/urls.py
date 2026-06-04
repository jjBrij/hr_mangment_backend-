# hrms_backend/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    # Comment out other apps for now
    # path('api/employees/', include('apps.employees.urls')),
    # path('api/attendance/', include('apps.attendance.urls')),
    # path('api/payroll/', include('apps.payroll.urls')),
    # path('api/leave/', include('apps.leave.urls')),
    # path('api/performance/', include('apps.performance.urls')),
]