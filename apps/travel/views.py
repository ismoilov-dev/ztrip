from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import generics, status
from apps.travel.travelserializers.travellistserializers import (
    TravelListSerializer,
    TravelWriteSerializers
)
from apps.location.models import Location
from .models import Travel, TravelLocation
from .serializers import TravelDetailSerializer

class TravelListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  
            return Travel.objects.none()
        return Travel.objects.filter(
            user=self.request.user
        ).prefetch_related(
            'travel_locations__location'
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TravelListSerializer
        return TravelWriteSerializers

class TravelDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Travel.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return TravelWriteSerializers   # ← yozish uchun
        return TravelDetailSerializer

class TravelLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Location qo'shish / olib tashlash / tartib",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove", "reorder"],
                        "example": "add"
                    },
                    "location_id":        {"type": "integer", "example": 3},
                    "visit_day":          {"type": "integer", "example": 1},
                    "order_index":        {"type": "integer", "example": 0},
                    "travel_location_id": {"type": "integer", "example": 5},
                    "order": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "travel_location_id": {"type": "integer"},
                                "visit_day":          {"type": "integer"},
                                "order_index":        {"type": "integer"},
                            }
                        }
                    },
                },
                "required": ["action"],
            }
        },
        responses={201: {"description": "Qo'shildi"}, 200: {"description": "OK"}},
    )
    def post(self, request, pk):
        travel = Travel.objects.filter(pk=pk, user=request.user).first()
        if not travel:
            return Response({'error': 'travel topilmadi! '}, status=404)
        action = request.data.get('action')
        # -- ADD --
        if action == 'add':
            location = Location.objects.filter(
                id=request.data.get('location_id')
            ).first()
            if not location:
                return Response({"error": "Location topilmadi."}, status=404)
            t1, created = TravelLocation.objects.get_or_create(
                travel=travel,
                location=location,
                defaults={
                    'visit_day': request.data.get('visit_day', 1),
                    'order_index': request.data.get('order_index', 0)
                },
            )
            if not created:
                return Response({'error': 'Allaqachon bor'}, status=400)
            return Response({"message": "Qo'shildi.", "id": t1.id}, status=201)
        # remove
        if action == "remove":
            TravelLocation.objects.filter(
                id=request.data.get('travel_location_id'),
                travel=travel,
            ).delete()
            return Response({'message': "O'chirildi! "})
        # reorder
        if action == "reorder":
            for item in request.data.get('order', []):
                TravelLocation.objects.filter(
                    id=item.get('travel_location_id'),
                    travel=travel
                ).update(
                    visit_day=item.get('visit_day', 1),
                    order_index=item.get("order_index", 0),
                )
            return Response({'message': 'Tartib yangilandi! '})
        return Response({"error": "action noto'g'ri."}, status=400)

class TravelStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Sayohat statusini o'zgartirish",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "completed", "cancelled"],
                        "example": "active",
                    },
                },
                "required": ["status"],
            }
        },
        responses={200: {"description": "Status o'zgartirildi"}},
    )
    def patch(self, request, pk):
        travel = Travel.objects.filter(pk=pk, user=request.user).first()
        if not travel:
            return Response({"error": "Travel topilmadi."}, status=404)

        if travel.status == "cancelled":
            return Response({"error": "Bekor qilingan travel o'zgartirilmaydi."}, status=400)

        new_status = request.data.get("status")
        if new_status not in ["active", "completed", "cancelled"]:
            return Response({"error": "Noto'g'ri status."}, status=400)

        travel.status = new_status
        travel.save(update_fields=["status"])
        return Response({"status": travel.status})