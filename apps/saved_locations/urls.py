from django.urls import path
from .views import SavedLocationView, SavedLocationDeleteView

urlpatterns = [
    path('saved_locations/', SavedLocationView.as_view()),
    path('saved_locations/delete/<int:pk>/', SavedLocationDeleteView.as_view()),
]
