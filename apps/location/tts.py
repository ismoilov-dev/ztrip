import io
import uuid
import boto3
from gtts import gTTS
from django.conf import settings


def text_to_speech(text: str, language: str = "uz") -> str:
    # uz → gtts da yo'q, ru ishlatamiz
    lang_map = {"uz": "ru", "ru": "ru", "en": "en"}
    gtts_lang = lang_map.get(language, "ru")

    # ── 1. gTTS orqali audio yaratish ────────────────────────
    tts = gTTS(text=text, lang=gtts_lang, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    # ── 2. MinIO ga saqlash ───────────────────────────────────
    filename  = f"audio/guide/{uuid.uuid4().hex}.mp3"
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )
    s3_client.upload_fileobj(
        audio_buffer,
        settings.AWS_STORAGE_BUCKET_NAME,
        filename,
        ExtraArgs={
            "ContentType": "audio/mpeg",
            "ACL": "public-read",
        },
    )

    # ── 3. URL qaytarish ──────────────────────────────────────
    return (
        f"{settings.AWS_S3_ENDPOINT_URL}"
        f"/{settings.AWS_STORAGE_BUCKET_NAME}"
        f"/{filename}"
    )