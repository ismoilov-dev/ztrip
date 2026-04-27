import re
from django.shortcuts import render
from django.utils import timezone
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.location.models import Location
from apps.travel.models import Travel, TravelLocation, TravelStatus
from .models import AIPlan, AIPlanStatus
from .serializers import (
    AIPlanGenerateSerializer, AIPlanApplySerializer,
    AIPlanSerializer, AudioGuideRequestSerializer,
    RecommendRequestSerializer,
)
from core.paginations import CustomPagination
from .prompt import (
    get_locations,
    TRAVEL_PLANNER_SYSTEM, travel_planner_prompt,
    AUDIO_GUIDE_SYSTEM,    audio_guide_prompt,
    RECOMMENDER_SYSTEM,    recommender_prompt,
)
from .ai_client import call_ai


def clean_cost(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    return float(cleaned) if cleaned else 0.0


class AIPlanViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = AIPlanSerializer
    pagination_class   = CustomPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AIPlan.objects.none()
        return AIPlan.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    @extend_schema(
        request=AIPlanGenerateSerializer,
        responses={201: AIPlanSerializer},
        summary="AI orqali marshrut generatsiyasi",
    )
    @action(detail=False, methods=["POST"], url_path="generate")
    def generate(self, request):
        s = AIPlanGenerateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        locs   = get_locations(d["city"], list(d.get("interests", [])))
        user_p = travel_planner_prompt(
            city=d["city"], days=d["days"],
            budget=d.get("budget"),
            interests=list(d.get("interests", [])),
            language=d.get("language", "uz"),
            locations=locs,
        )

        try:
            plan_json, model = call_ai(
                TRAVEL_PLANNER_SYSTEM, user_p, max_tokens=2500
            )
        except RuntimeError as e:
            return Response({"error": str(e)}, status=503)

        location_ids = [
            loc.get("id")
            for day in plan_json.get("days", [])
            for loc in day.get("locations", [])
            if loc.get("id")
        ]
        db_locations = {
            l.id: l
            for l in Location.objects.filter(id__in=location_ids)
        }

        for day in plan_json.get("days", []):
            for loc in day.get("locations", []):
                loc_id = loc.get("id")
                if loc_id in db_locations:
                    db_loc = db_locations[loc_id]
                    loc["name"]  = db_loc.name
                    loc["lat"]   = float(db_loc.latitude)  if db_loc.latitude  else None
                    loc["lng"]   = float(db_loc.longitude) if db_loc.longitude else None
                    loc["image"] = db_loc.image.url if db_loc.image else None

        ai_plan = AIPlan.objects.create(
            user=request.user,
            city=d["city"],
            days=d["days"],
            budget=d.get("budget"),
            interests=list(d.get("interests", [])),
            language=d.get("language", "uz"),
            status=AIPlanStatus.COMPLETED,
            plan_json=plan_json,
            ai_model_used=model,
            prompt_used=user_p,
        )
        return Response(
            AIPlanSerializer(ai_plan).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=AIPlanApplySerializer,
        summary="AI planni Travel ga aylantirish",
    )
    @action(detail=True, methods=["POST"], url_path="apply")
    def apply(self, request, pk=None):
        try:
            ai_plan = AIPlan.objects.get(
                pk=pk, user=request.user, travel__isnull=True
            )
        except AIPlan.DoesNotExist:
            return Response(
                {"error": "Plan topilmadi yoki allaqachon qo'llangan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        s = AIPlanApplySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d    = s.validated_data
        plan = ai_plan.plan_json

        travel = Travel.objects.create(
            user=request.user,
            title=f"{ai_plan.city} — {ai_plan.days} kun",
            start_date=d["start_date"],
            end_date=d["end_date"],
            budget=clean_cost(plan.get("total_cost", 0)),
            status=TravelStatus.DRAFT,
        )

        for day_data in plan.get("days", []):
            for idx, loc in enumerate(day_data.get("locations", [])):
                location = Location.objects.filter(id=loc["id"]).first()
                if location:
                    TravelLocation.objects.get_or_create(
                        travel=travel,
                        location=location,
                        defaults={
                            "visit_day": day_data["day"],
                            "order_index": idx,
                        },
                    )

        ai_plan.travel = travel
        ai_plan.status = AIPlanStatus.APPLIED
        ai_plan.save(update_fields=["travel", "status"])

        return Response({
            "travel_id": travel.id,
            "title": travel.title,
            "message": "Travel muvaffaqiyatli yaratildi!",
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=RecommendRequestSerializer,
        summary="Shaxsiy joy tavsiyalari",
    )
    @action(detail=False, methods=["POST"], url_path="recommend")
    def recommend(self, request):
        s = RecommendRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        visited_ids = list(
            TravelLocation.objects
            .filter(travel__user=request.user)
            .values_list("location_id", flat=True)
            .distinct()
        )
        locs   = get_locations(d["city"], list(d.get("interests", [])))
        user_p = recommender_prompt(
            interests=list(d.get("interests", [])),
            visited_ids=visited_ids,
            locations=locs,
            language=d.get("language", "uz"),
        )

        try:
            result, _ = call_ai(RECOMMENDER_SYSTEM, user_p, max_tokens=1000)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=503)

        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        request=AudioGuideRequestSerializer,
        summary="Location uchun AI audio gid skripti",
    )
    @action(detail=True, methods=["POST"], url_path="audio-guide")
    def audio_guide(self, request, pk=None):
        s = AudioGuideRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        location = Location.objects.filter(id=pk).first()
        if not location:
            return Response({"error": "Location topilmadi."}, status=404)

        language = s.validated_data.get("language", "uz")
        user_p   = audio_guide_prompt(
            location_id=location.id,
            name=location.name,
            loc_type=location.get_type_display(),
            description=location.description,
            language=language,
        )

        try:
            result, _ = call_ai(AUDIO_GUIDE_SYSTEM, user_p, max_tokens=1000)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=503)

        script = result.get("script", "")

        if script:
            from apps.location.tasks import generate_audio_task
            generate_audio_task.delay(location.id, script, language)

        return Response({
            "script": result,
            "audio_status": "processing" if script else "no_script",
            "message": "Audio yaratilmoqda, biroz kuting...",
        }, status=200)