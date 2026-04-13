import logging
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger("location")


@shared_task(bind=True, max_retries=3)
def generate_audio_task(self, location_id: int, script: str, lang: str = "uz"):
    """
    Background da audio yaratadi va location ga saqlaydi.

    Args:
        location_id: Location pk
        script: AI tomonidan yaratilgan audio guide matni
        lang: til kodi (uz, ru, en)
    """
    try:
        from .models import Location
        from .tts import text_to_speech

        location = Location.objects.get(pk=location_id)

        # ElevenLabs → MinIO → URL
        audio_url = text_to_speech(script, lang)

        # location.audio URLField ga saqlaydi
        location.audio_url = audio_url
        location.save(update_fields=["audio_url"])

        logger.info(
            f"[TTS] Location {location_id} audio tayyor: {audio_url}"
        )
        return {
            "status": "done",
            "location_id": location_id,
            "audio_url": audio_url,
        }

    except ObjectDoesNotExist:
        logger.error(f"[TTS] Location {location_id} topilmadi")
        return {
            "status": "error",
            "message": "Location topilmadi",
        }

    except Exception as exc:
        logger.error(
            f"[TTS] Location {location_id} xatolik: {exc}"
        )
        raise self.retry(exc=exc, countdown=30)
        # 30 soniyadan keyin qayta urinadi (3 marta)