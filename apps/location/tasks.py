from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist


@shared_task(bind=True, max_retries=3)
def generate_audio_task(self, location_id: int, lang: str = "ru"):
    try:
        from .models import Location
        from .ai_audio import audio_guide

        location = Location.objects.get(pk=location_id)

        audio_file = audio_guide.generate(
            text=location.description,
            location_id=location.pk,
            lang=lang,
        )
        location.audio = audio_file
        location.save(update_fields=["audio"])

        return {"status": "done", "location_id": location_id}

    except ObjectDoesNotExist:
        return {"status": "error", "message": "Location topilmadi"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)