from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIPlanViewSet, audio_guide_view

router = DefaultRouter()
router.register(r"ai-plans", AIPlanViewSet, basename="ai-plans")

urlpatterns = [
    path("audio-guide/", audio_guide_view, name="audio-guide"),
    path("", include(router.urls)),
]