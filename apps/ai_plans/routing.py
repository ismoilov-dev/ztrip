from django.urls import path
from .consumers import LiveGuideConsumer

websocket_urlpatterns = [
    path("ws/live-guide/", LiveGuideConsumer.as_asgi()),
]