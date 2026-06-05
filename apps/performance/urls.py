# apps/performance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter,SimpleRouter
from . import views

# Create router
router = SimpleRouter()
router.register(r'targets', views.PerformanceTargetViewSet, basename='performance-targets')
router.register(r'daily', views.DailyTargetViewSet, basename='daily-targets')
router.register(r'reviews', views.PerformanceReviewViewSet, basename='performance-reviews')

urlpatterns = [
    path('', include(router.urls)),
]