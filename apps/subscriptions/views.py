from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Subscription
from .serializers import SubscriptionSerializers
from core.paginations import CustomPagination


@extend_schema_view(
    get=extend_schema(summary="Subscriptionlar ro'yxati"),
    post=extend_schema(summary="Subscription qo'shish"),
)
class SubscriptionCreateListApiView(generics.ListCreateAPIView):
    serializer_class   = SubscriptionSerializers
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subscription.objects.none()
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(summary="Subscription detail"),
    delete=extend_schema(summary="Subscriptionni deactivate qilish"),
)
class SubscriptionRetrieveUpdateDestroyAPIView(generics.RetrieveDestroyAPIView):
    serializer_class   = SubscriptionSerializers
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subscription.objects.none()
        return Subscription.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.deactivate()