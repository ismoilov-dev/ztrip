from rest_framework import serializers
from .models import Location


# ─── constants ────────────────────────────────────────────────────────────────

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg"]
MAX_IMAGE_SIZE      = 10 * 1024 * 1024   # 10 MB
MAX_AUDIO_SIZE      = 50 * 1024 * 1024   # 50 MB


# ─── helpers ──────────────────────────────────────────────────────────────────

def _absolute_url(request, file_field):
    """Return absolute URL for a file field, or None if empty."""
    if not file_field:
        return None
    url = file_field.url
    return request.build_absolute_uri(url) if request else url


def _validate_file(value, allowed_types, max_size, type_label):
    if value is None:
        return value
    if value.content_type not in allowed_types:
        raise serializers.ValidationError(
            f"Ruxsat etilgan formatlar: {', '.join(allowed_types)}"
        )
    if value.size > max_size:
        raise serializers.ValidationError(
            f"Maksimal hajm: {max_size // (1024 * 1024)} MB"
        )
    return value


# ─── upload-only serializers (swagger choose-file) ────────────────────────────

class ImageUploadSerializer(serializers.Serializer):
    file = serializers.ImageField()


class AudioUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


# ─── list ─────────────────────────────────────────────────────────────────────

class LocationListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    image        = serializers.SerializerMethodField()

    class Meta:
        model  = Location
        fields = [
            "id", "name", "city", "country",
            "type", "type_display",
            "image", "price", "is_premium",
            "latitude", "longitude",
        ]

    def get_image(self, obj):
        return _absolute_url(self.context.get("request"), obj.image)


# ─── detail ───────────────────────────────────────────────────────────────────

class LocationDetailSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    image        = serializers.SerializerMethodField()
    audio        = serializers.SerializerMethodField()

    class Meta:
        model  = Location
        fields = [
            "id", "name", "description",
            "image", "audio",
            "price", "country", "city",
            "latitude", "longitude",
            "type", "type_display",
            "is_premium", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_image(self, obj):
        return _absolute_url(self.context.get("request"), obj.image)

    def get_audio(self, obj):
        if not obj.audio:
            return None

        # Free content — always visible
        if not obj.is_premium:
            return _absolute_url(self.context.get("request"), obj.audio)

        # Premium content — only for active subscribers
        request = self.context.get("request")
        if (
            request
            and request.user.is_authenticated
            # and request.user.subscriptions.filter(is_active=True).exists()
        ):
            return _absolute_url(request, obj.audio)

        return None


# ─── write (create / update) ──────────────────────────────────────────────────

class LocationWriteSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    audio = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model  = Location
        fields = [
            "id", "name", "description",
            "image", "audio",
            "price", "country", "city",
            "latitude", "longitude",
            "type", "is_premium",
        ]
        read_only_fields = ["id"]

    def validate_image(self, value):
        return _validate_file(value, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, "rasm")

    def validate_audio(self, value):
        return _validate_file(value, ALLOWED_AUDIO_TYPES, MAX_AUDIO_SIZE, "audio")

    def to_representation(self, instance):
        """Create/update dan keyin DetailSerializer qaytaradi."""
        return LocationDetailSerializer(instance, context=self.context).data