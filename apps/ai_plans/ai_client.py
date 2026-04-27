import json
import logging
import time
import google.genai as genai

logger = logging.getLogger("ai_plans")

FALLBACK_MODELS = [
    "models/gemini-flash-latest",   # ← birinchi — ishlayapti
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
]

def get_client():
    from django.conf import settings
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def clean_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)

def call_ai(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> tuple[dict, str]:
    client     = get_client()
    last_error = None
    full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"

    for model in FALLBACK_MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                )
                result = clean_json(response.text)
                logger.info(f"[AI] {model} ishlatildi")
                return result, model

            except json.JSONDecodeError as e:
                logger.error(f"[AI] {model} JSON xato: {e}")
                last_error = e
                break  # JSON xato bo'lsa keyingi modelga

            except Exception as e:
                error_str = str(e)
                last_error = e
                logger.error(f"[AI] {model} xatolik (urinish {attempt+1}): {e}")

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # quota tugagan — keyingi modelga o'tamiz
                    break

                if "503" in error_str or "UNAVAILABLE" in error_str:
                    if attempt < 2:
                        time.sleep(5)
                        continue
                    break

                if "404" in error_str or "NOT_FOUND" in error_str:
                    break  # model yo'q — keyingisiga

                time.sleep(2)
                break

    raise RuntimeError(f"Barcha modellar ishlamadi. Xatolik: {last_error}")