# apps/users/tests/test_views.py
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

User = get_user_model()


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@test.com",
        full_name="Test User",
        country="Uzbekistan",
        language_code="en",
    )


@pytest.fixture
def google_idinfo():
    """Fake Google token payload"""
    return {
        "email":   "google@test.com",
        "name":    "Google User",
        "picture": "https://example.com/avatar.jpg",
        "aud":     "test-client-id",
    }


# ── Google Auth ───────────────────────────────────────────────────────────────

class TestGoogleAuthView:

    def test_token_yoq_400(self, api_client, db):
        res = api_client.post("/auth/google/", {})
        assert res.status_code == 400

    def test_yaroqsiz_token_400(self, api_client, db):
        with patch("apps.users.serializers.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Token noto'g'ri")
            res = api_client.post("/auth/google/", {"token": "fake-token"})
        assert res.status_code == 400
        assert "Token yaroqsiz" in str(res.data)

    def test_yangi_user_201(self, api_client, db, google_idinfo):
        with patch("apps.users.serializers.id_token.verify_oauth2_token") as mock_verify:
            with patch("apps.users.serializers.settings") as mock_settings:
                mock_settings.SOCIALACCOUNT_PROVIDERS = {
                    "google": {"APP": {"client_id": "test-client-id"}}
                }
                mock_verify.return_value = google_idinfo
                res = api_client.post("/auth/google/", {"token": "valid-token"})

        assert res.status_code == 201
        assert res.data["created"] is True
        assert res.data["user"]["email"] == "google@test.com"
        assert "tokens" in res.data
        assert "access" in res.data["tokens"]
        assert "refresh" in res.data["tokens"]

    def test_mavjud_user_200(self, api_client, db, google_idinfo):
        User.objects.create_user(email="google@test.com", full_name="Old Name")

        with patch("apps.users.serializers.id_token.verify_oauth2_token") as mock_verify:
            with patch("apps.users.serializers.settings") as mock_settings:
                mock_settings.SOCIALACCOUNT_PROVIDERS = {
                    "google": {"APP": {"client_id": "test-client-id"}}
                }
                mock_verify.return_value = google_idinfo
                res = api_client.post("/auth/google/", {"token": "valid-token"})

        assert res.status_code == 200
        assert res.data["created"] is False

    def test_is_new_user_false_qilinadi(self, api_client, db, google_idinfo):
        existing = User.objects.create_user(
            email="google@test.com",
            is_new_user=True,
        )
        with patch("apps.users.serializers.id_token.verify_oauth2_token") as mock_verify:
            with patch("apps.users.serializers.settings") as mock_settings:
                mock_settings.SOCIALACCOUNT_PROVIDERS = {
                    "google": {"APP": {"client_id": "test-client-id"}}
                }
                mock_verify.return_value = google_idinfo
                api_client.post("/auth/google/", {"token": "valid-token"})

        existing.refresh_from_db()
        assert existing.is_new_user is False


# ── Me (GET /auth/me/) ────────────────────────────────────────────────────────

class TestMeView:

    def test_loginsiz_401(self, api_client):
        res = api_client.get("/auth/me/")
        assert res.status_code == 401

    def test_login_qilgan_user_malumotlari(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.get("/auth/me/")
        assert res.status_code == 200
        assert res.data["email"]     == "user@test.com"
        assert res.data["full_name"] == "Test User"
        assert res.data["country"]   == "Uzbekistan"

    def test_kerakli_fieldlar_bor(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.get("/auth/me/")
        for field in ["id", "email", "full_name", "avatar_url", "country", "language_code", "created_at", "is_new_user"]:
            assert field in res.data

    def test_readonly_fieldlar_ozgarmaydi(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch("/auth/me/", {"email": "hacker@evil.com", "is_new_user": False})
        assert res.status_code == 200
        assert res.data["email"] == "user@test.com"   # o'zgarmagan


# ── Me (PATCH /auth/me/) ──────────────────────────────────────────────────────

class TestMeUpdateView:

    def test_loginsiz_401(self, api_client):
        res = api_client.patch("/auth/me/", {"full_name": "Yangi Ism"})
        assert res.status_code == 401

    def test_full_name_ozgartirish(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch("/auth/me/", {"full_name": "Yangi Ism"})
        assert res.status_code == 200
        assert res.data["full_name"] == "Yangi Ism"

    def test_language_code_ozgartirish(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch("/auth/me/", {"language_code": "ru"})
        assert res.status_code == 200
        assert res.data["language_code"] == "ru"

    def test_country_ozgartirish(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch("/auth/me/", {"country": "Russia"})
        assert res.status_code == 200
        assert res.data["country"] == "Russia"

    def test_partial_update_boshqa_fieldlar_saqlanadi(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch("/auth/me/", {"country": "Russia"})
        assert res.status_code == 200
        assert res.data["full_name"] == "Test User"   # o'zgarmagan
        