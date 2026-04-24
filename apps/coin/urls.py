from django.urls import path
from .views import UserCoinView

urlpatterns = [
    path('<int:user_id>/', UserCoinView.as_view(), name='user-coin'),
]