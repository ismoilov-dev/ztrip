from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from core.permissions import IsAdminOrReadOnly
from core.paginations import CustomPagination
from .models import Location
from .tasks import generate_audio_task  # ← bitta import
from .serializers import (
    LocationDetailSerializer,
    LocationListSerializer,
    LocationWriteSerializer,
)


@method_decorator(cache_page(60 * 15), name="list")  # 15 daqiqa cache
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

    @extend_schema(
        request=None,
        responses={202: None, 200: None, 400: None, 403: None},
        summary="AI orqali audio guide yaratish (background)",
    )
    @action(detail=True, methods=["POST"], url_path="generate-audio")
    def generate_audio(self, request, pk=None):
        location = self.get_object()

        if not location.description:
            return Response({"error": "Description yo'q."}, status=400)

        if location.is_premium and not request.user.is_staff:
            return Response({"error": "Faqat admin."}, status=403)

        # Allaqachon audio bor bo'lsa qayta yaratma
        if location.audio:
            return Response({
                "message": "Audio allaqachon bor.",
                "audio": request.build_absolute_uri(location.audio.url),
            }, status=200)

        lang = request.query_params.get("lang", "uz")

        # Background da — user kutmaydi
        generate_audio_task.delay(location.id, location.description, lang)

        return Response({
            "message": "Audio yaratilmoqda...",
            "location_id": location.id,
        }, status=202)

    @extend_schema(
        parameters=[
            OpenApiParameter("lat",    float, required=True),
            OpenApiParameter("lng",    float, required=True),
            OpenApiParameter("radius", float, required=False),
        ],
        summary="Yaqin atrofdagi locationlar",
    )
    @action(detail=False, methods=["GET"], url_path="nearby")
    def nearby(self, request):
        lat    = request.query_params.get("lat")
        lng    = request.query_params.get("lng")
        radius = float(request.query_params.get("radius", 5))

        if not lat or not lng:
            return Response({"error": "lat va lng kerak."}, status=400)

        lat, lng = float(lat), float(lng)
        delta    = radius / 111.0

        locations = Location.objects.filter(
            latitude__range=(lat - delta, lat + delta),
            longitude__range=(lng - delta, lng + delta),
        )
        serializer = LocationListSerializer(
            locations, many=True, context={"request": request}
        )
        return Response(serializer.data)