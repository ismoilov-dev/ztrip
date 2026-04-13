from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import SavedLocationSerializer
from .models import SavedLocation
from core.paginations import CustomPagination


class SavedLocationView(generics.ListCreateAPIView):
    serializer_class = SavedLocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SavedLocation.objects.none()
        return SavedLocation.objects.filter(user=self.request.user).order_by('-created_at')


class SavedLocationDeleteView(generics.DestroyAPIView):
    serializer_class = SavedLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SavedLocation.objects.none()
        return SavedLocation.objects.filter(user=self.request.user)