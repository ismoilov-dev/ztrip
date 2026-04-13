import re
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


def is_premium(user):
    return user.subscriptions.filter(
        plan="premium",
        is_active=True,
    ).exists()


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

    # ── GET /ai-plans/  +  GET /ai-plans/{id}/ ────────────────
    # ListModelMixin + RetrieveModelMixin orqali avtomatik

    # ── POST /ai-plans/generate/ ──────────────────────────────
    @extend_schema(
        request=AIPlanGenerateSerializer,
        responses={201: AIPlanSerializer},
        summary="AI orqali marshrut generatsiyasi",
    )
    @action(detail=False, methods=["POST"], url_path="generate")
    def generate(self, request):
        # Free user — kuniga 3ta limit
        if not is_premium(request.user):
            today_count = AIPlan.objects.filter(
                user=request.user,
                created_at__date=timezone.now().date(),
            ).count()
            if today_count >= 3:
                return Response(
                    {"error": "Kunlik limit 3ta. Premium oling."},
                    status=status.HTTP_403_FORBIDDEN,
                )

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

    # ── POST /ai-plans/{id}/apply/ ────────────────────────────
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
            budget=clean_cost(plan.get("total_estimated_cost", 0)),
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

    # ── POST /ai-plans/recommend/ ─────────────────────────────
    @extend_schema(
        request=RecommendRequestSerializer,
        summary="Shaxsiy joy tavsiyalari",
    )
    @action(detail=False, methods=["POST"], url_path="recommend")
    def recommend(self, request):
        # Premium only
        if not is_premium(request.user):
            return Response(
                {"error": "Tavsiyalar faqat premium foydalanuvchilar uchun."},
                status=status.HTTP_403_FORBIDDEN,
            )

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

    # ── POST /ai-plans/{id}/audio-guide/ ──────────────────────
    @extend_schema(
        request=AudioGuideRequestSerializer,
        summary="Location uchun AI audio gid skripti",
    )
    @action(detail=True, methods=["POST"], url_path="audio-guide")
    def audio_guide(self, request, pk=None):
        # Premium only
        if not is_premium(request.user):
            return Response(
                {"error": "Audio guide faqat premium foydalanuvchilar uchun."},
                status=status.HTTP_403_FORBIDDEN,
            )

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