from django.urls import path
from .views import SubscriptionCreateListApiView, SubscriptionRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('subscription/', SubscriptionCreateListApiView.as_view()),
    path('subscription/<int:pk>/', SubscriptionRetrieveUpdateDestroyAPIView.as_view()),

]
