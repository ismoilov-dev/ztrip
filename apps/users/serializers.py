from rest_framework import serializers
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from .models import User


LANGUAGE_CHOICES = ["en", "ru", "ar"]


class GoogleAuthSerializer(serializers.Serializer):
    token         = serializers.CharField(required=True)
    language_code = serializers.ChoiceField(
        choices=LANGUAGE_CHOICES,
        default="en",
        required=False,
    )

    def validate_token(self, token):
        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                client_id,
                clock_skew_in_seconds=10,
            )
        except ValueError as e:
            raise serializers.ValidationError(f"Token yaroqsiz: {e}")

        if idinfo.get("aud") != client_id:
            raise serializers.ValidationError("Token boshqa ilovaga tegishli.")

        return idinfo

    def get_or_create_user(self):
        idinfo        = self.validated_data["token"]
        language_code = self.validated_data.get("language_code", "en")

        email      = idinfo.get("email", "")
        full_name  = idinfo.get("name", "")
        avatar_url = idinfo.get("picture", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name":     full_name,
                "avatar_url":    avatar_url,
                "language_code": language_code,
                "is_active":     True,
                "is_new_user":   True,
            },
        )

        if not created:
            update_fields = []

            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                update_fields.append("avatar_url")

            if user.is_new_user:
                user.is_new_user = False
                update_fields.append("is_new_user")

            if update_fields:
                user.save(update_fields=update_fields)

        return user, created


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model        = User
        fields       = ["id", "email", "full_name", "avatar_url", "country", "language_code", "created_at", "is_new_user"]
        read_only_fields = ["id", "email", "created_at", "is_new_user"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """PATCH /auth/me/ uchun"""
    class Meta:
        model  = User
        fields = ["full_name", "avatar_url", "country", "language_code"]

class LoginSerializers(serializers.Serializer):
    email = serializers.EmailField()
    avatar_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)


class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Foydalanuvchi emaili"
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6 xonali tasdiqlash kodi",
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Kod faqat raqamlardan iborat bo'lishi kerak.")
        return value