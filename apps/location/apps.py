from django.apps import AppConfig


class LocationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.location"

    def ready(self):
        # Django start bo'lganda bucket tekshiriladi/yaratiladi
        try:
            from .utils import ensure_bucket_exists
            ensure_bucket_exists()
        except Exception as e:
            print(f"MinIO ulanmadi: {e}")