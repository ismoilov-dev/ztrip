from django.urls import path
from .views import (
    TravelListCreateView,
    TravelDetailView,
    TravelLocationView,
    TravelStatusView,
)

urlpatterns = [
    path("travel/",                    TravelListCreateView.as_view()),
    path("travel/<int:pk>/",           TravelDetailView.as_view()),
    path("travel/<int:pk>/locations/", TravelLocationView.as_view()),
    path("travel/<int:pk>/status/",    TravelStatusView.as_view()),
]