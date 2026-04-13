import io
import uuid
import requests
import boto3
from django.conf import settings


def text_to_speech(text: str, language: str = "uz") -> str:
    """
    ElevenLabs orqali matnni audio ga aylantiradi,
    MinIO ga saqlaydi va URL qaytaradi.
    """
    # ── 1. ElevenLabs API ────────────────────────────────────
    voice_id = settings.ELEVENLABS_VOICE_ID
    url      = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # uz/ru/en hammasi
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()

    audio_bytes = response.content  # mp3 bytes

    # ── 2. MinIO ga saqlash ───────────────────────────────────
    filename   = f"audio/guide/{uuid.uuid4().hex}.mp3"
    s3_client  = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )

    s3_client.upload_fileobj(
        io.BytesIO(audio_bytes),
        settings.AWS_STORAGE_BUCKET_NAME,
        filename,
        ExtraArgs={
            "ContentType": "audio/mpeg",
            "ACL": "public-read",
        },
    )

    # ── 3. URL qaytarish ──────────────────────────────────────
    audio_url = (
        f"{settings.AWS_S3_ENDPOINT_URL}"
        f"/{settings.AWS_STORAGE_BUCKET_NAME}"
        f"/{filename}"
    )
    return audio_url