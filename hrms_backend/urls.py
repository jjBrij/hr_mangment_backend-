from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('api/auth/', include('apps.accounts.urls')),
   
   
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('api/employees/', include('apps.employees.urls')),  
    path('api/performance/', include('apps.performance.urls')),
  #  path('api/leave/', include('apps.leave.urls')),          # ← ADD
  #  path('api/payroll/', include('apps.payroll.urls')),      # ← ADD
  #  path('api/attendance/', include('apps.attendance.urls')), # ← ADD
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)