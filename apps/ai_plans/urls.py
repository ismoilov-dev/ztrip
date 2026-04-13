from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIPlanViewSet

router = DefaultRouter()
router.register(r"ai-plans", AIPlanViewSet, basename="ai-plans")

urlpatterns = [path("", include(router.urls))]