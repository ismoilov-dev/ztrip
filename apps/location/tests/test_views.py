import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.location.models import Location

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@test.com",
        password="admin123",
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="user123",
    )


@pytest.fixture
def location(db):
    return Location.objects.create(
        name="Registon",
        description="Samarqand shahridagi tarixiy maydon.",
        country="Uzbekistan",
        city="Samarqand",
        latitude=39.6542,
        longitude=66.9758,
        is_premium=False,
    )


@pytest.fixture
def premium_location(db):
    return Location.objects.create(
        name="Shoh-i-Zinda",
        description="Premium tarixiy joy.",
        country="Uzbekistan",
        city="Samarqand",
        latitude=39.6600,
        longitude=66.9800,
        is_premium=True,
    )


# ── LIST ──────────────────────────────────────────────────────────────────────

class TestLocationList:
    def test_anonim_list_kora_oladi(self, api_client, location):
        res = api_client.get("/locations/")
        assert res.status_code == 200

    def test_pagination_ishlaydi(self, api_client, location):
        res = api_client.get("/locations/")
        assert "results" in res.data
        assert "count" in res.data


# ── CREATE ────────────────────────────────────────────────────────────────────

class TestLocationCreate:
    def test_anonim_yarata_olmaydi(self, api_client):
        res = api_client.post("/locations/", {"name": "Test"})
        assert res.status_code == 401

    def test_oddiy_user_yarata_olmaydi(self, api_client, regular_user):
        api_client.force_authenticate(user=regular_user)
        res = api_client.post("/locations/", {"name": "Test"})
        assert res.status_code == 403

    def test_admin_yarata_oladi(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        res = api_client.post("/locations/", {
            "name": "Test Joy",
            "description": "Test description",
            "country": "Uzbekistan",
            "city": "Toshkent",
            "latitude": 41.2995,
            "longitude": 69.2401,
            "type": "historical",   # ✅ mosque → historical
            "is_premium": False,
        })
        assert res.status_code == 201
        assert res.data["name"] == "Test Joy"


# ── DETAIL ────────────────────────────────────────────────────────────────────

class TestLocationDetail:
    def test_barchasi_kora_oladi(self, api_client, location):
        res = api_client.get(f"/locations/{location.pk}/")
        assert res.status_code == 200
        assert res.data["name"] == location.name

    def test_free_audio_hamma_koradi(self, api_client, regular_user, location):
        location.audio = "test/audio.mp3"
        location.save()
        api_client.force_authenticate(user=regular_user)
        res = api_client.get(f"/locations/{location.pk}/")
        assert res.data["audio"] is not None

    def test_premium_audio_loginsiz_null(self, api_client, premium_location):
        premium_location.audio = "test/audio.mp3"
        premium_location.save()
        res = api_client.get(f"/locations/{premium_location.pk}/")
        assert res.data["audio"] is None


# ── GENERATE AUDIO ────────────────────────────────────────────────────────────

class TestGenerateAudio:
    def test_description_yoq_400(self, api_client, admin_user, db):
        api_client.force_authenticate(user=admin_user)
        loc = Location.objects.create(
            name="Test", country="UZ", city="Toshkent",
            latitude=41.0, longitude=69.0, is_premium=False,
        )
        res = api_client.post(f"/locations/{loc.pk}/generate-audio/")
        assert res.status_code == 400

    def test_premium_user_yarata_olmaydi(self, api_client, regular_user, premium_location):
        api_client.force_authenticate(user=regular_user)
        res = api_client.post(f"/locations/{premium_location.pk}/generate-audio/")
        assert res.status_code == 403

    def test_admin_background_task_boshlaydi(self, api_client, admin_user, location):
        api_client.force_authenticate(user=admin_user)
        res = api_client.post(f"/locations/{location.pk}/generate-audio/")
        assert res.status_code == 202
        assert res.data["status"] == "processing"
        assert "task_id" in res.data