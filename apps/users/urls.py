from django.urls import path
from .views import GoogleAuthView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
    # path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("login/", LoginView.as_view(), name="login"),
    # path("auth/me/",     MeView.as_view(),         name="me"),
]