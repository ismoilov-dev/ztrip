from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from core.permissions import IsAdminOrReadOnly
from core.paginations import CustomPagination
from .models import Location
from .tasks import generate_audio_task
from .serializers import (
    AudioUploadSerializer,
    ImageUploadSerializer,
    LocationDetailSerializer,
    LocationListSerializer,
    LocationWriteSerializer,
)


class LocationViewSet(ModelViewSet):
    queryset           = Location.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    pagination_class   = CustomPagination

    def get_serializer_class(self):
        if self.action == "list":
            return LocationListSerializer
        if self.action in ("create", "update", "partial_update"):
            return LocationWriteSerializer
        return LocationDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @extend_schema(request=ImageUploadSerializer, responses={200: LocationDetailSerializer}, summary="Rasm yuklash (MinIO)")
    @action(detail=True, methods=["POST"], url_path="upload-image", parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        location = self.get_object()
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        location.image = serializer.validated_data["file"]
        location.save(update_fields=["image"])
        return Response(LocationDetailSerializer(location, context={"request": request}).data, status=status.HTTP_200_OK)

    @extend_schema(request=AudioUploadSerializer, responses={200: LocationDetailSerializer}, summary="Audio yuklash (MinIO)")
    @action(detail=True, methods=["POST"], url_path="upload-audio", parser_classes=[MultiPartParser, FormParser])
    def upload_audio(self, request, pk=None):
        location = self.get_object()
        serializer = AudioUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        location.audio = serializer.validated_data["file"]
        location.save(update_fields=["audio"])
        return Response(LocationDetailSerializer(location, context={"request": request}).data, status=status.HTTP_200_OK)

    @extend_schema(request=None, responses={202: None, 400: None, 403: None}, summary="AI orqali audio guide yaratish (background)")
    @action(detail=True, methods=["POST"], url_path="generate-audio")
    def generate_audio(self, request, pk=None):
        location = self.get_object()

        if not location.description:
            return Response({"error": "Description yo'q."}, status=400)

        if location.is_premium and not request.user.is_staff:
            return Response({"error": "Faqat admin."}, status=403)

        lang = request.query_params.get("lang", "en")

        # Celery o'rniga to'g'ridan-to'g'ri (sekinroq lekin ishonchli)
        from .ai_audio import audio_guide
        audio_file = audio_guide.generate(text=location.description, location_id=location.pk, lang=lang)
        location.audio = audio_file
        location.save(update_fields=["audio"])

        return Response(
            LocationDetailSerializer(location, context={"request": request}).data,
            status=200,
        )
