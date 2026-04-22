import asyncio
import io
import edge_tts
import openai
import requests
from django.conf import settings
from django.core.files.base import ContentFile


class AudioGuideGenerator:

    def generate(self, text: str, location_id: int, lang: str = "ru") -> ContentFile:
        provider = settings.AI_PROVIDER

        generators = {
            "gtts":       lambda t: self._edge_tts(t, lang),
            "gemini":     lambda t: self._edge_tts(t, lang),
            "openai":     self._openai,
            "elevenlabs": self._elevenlabs,
        }

        if provider not in generators:
            raise ValueError(f"Noto'g'ri AI_PROVIDER: {provider}")

        audio_bytes = generators[provider](text)
        return ContentFile(audio_bytes, name=f"audio_guide_{location_id}.mp3")

    # ── Edge TTS (Microsoft, bepul, tez ~1-2s) ───────────────────────────────
    def _edge_tts(self, text: str, lang: str = "ru") -> bytes:
        voices = {
        "en": "en-US-ChristopherNeural",
        "ru": "ru-RU-SvetlanaNeural",
        "uz": "uz-UZ-MadinaNeural",
    }
        voice = voices.get(lang, "uz-UZ-MadinaNeural")

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            return buffer.getvalue()

        return asyncio.run(_generate())

    # ── OpenAI ────────────────────────────────────────────────────────────────
    def _openai(self, text: str) -> bytes:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        return response.content

    # ── ElevenLabs ────────────────────────────────────────────────────────────
    def _elevenlabs(self, text: str) -> bytes:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key":   settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text":     text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability":        0.5,
                    "similarity_boost": 0.75,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.content


audio_guide = AudioGuideGenerator()