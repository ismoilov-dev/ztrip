from rest_framework import serializers
from .models import AIPlan


class AIPlanGenerateSerializer(serializers.Serializer):
    city      = serializers.CharField(max_length=100)
    days      = serializers.IntegerField(min_value=1, max_value=30)
    budget    = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        required=False, allow_null=True,
    )
    interests = serializers.MultipleChoiceField(
        choices=[
            "historical", "nature", "museum",
            "restaurant", "entertainment", "park",
        ],
        required=False, default=set,
    )
    language  = serializers.ChoiceField(
        choices=["uz", "ru", "en"],
        default="uz",
    )
class AIPlanApplySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date   = serializers.DateField()

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "Tugash sanasi boshlanishdan oldin bo'lishi mumkin emas."}
            )
        return attrs


class AIPlanSerializer(serializers.ModelSerializer):
    is_applied = serializers.BooleanField(read_only=True)

    class Meta:
        model = AIPlan
        fields = [
            "id",
            "city",
            "days",
            "budget",
            "interests",
            "language",
            "status",
            "is_applied",
            "plan_json",
            "ai_model_used",
            "travel",
            "created_at",
        ]
        read_only_fields = fields


class AudioGuideRequestSerializer(serializers.Serializer):
    location_id = serializers.IntegerField(
        min_value=1,
        help_text="Location ID (masalan: 1, 2, 3)",
    )
    language = serializers.ChoiceField(
        choices=["uz", "ru", "en"],
        default="uz",
    )


class RecommendRequestSerializer(serializers.Serializer):
    city      = serializers.CharField(max_length=100)
    language  = serializers.ChoiceField(
        choices=["uz", "ru", "en"],
        default="uz",
    )
    interests = serializers.MultipleChoiceField(
        choices=[
            "historical", "nature", "museum",
            "restaurant", "entertainment", "park",
        ],
        required=False, default=set,
    )