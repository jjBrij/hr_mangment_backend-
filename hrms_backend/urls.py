
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('api/auth/', include('apps.accounts.urls')),
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('api/employees/', include('apps.employees.urls')),  
    path('api/performance/', include('apps.performance.urls')),  # Add this


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)