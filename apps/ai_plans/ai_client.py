import json
import logging
import time
import google.genai as genai

logger = logging.getLogger("ai_plans")

FALLBACK_MODELS = [
    "models/gemini-1.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash",
    "models/gemini-1.5-pro",
    "models/gemini-flash-latest",
]


def get_client():
    from django.conf import settings
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return client


def clean_json(text: str) -> dict:
    # markdown ```json ... ``` ni tozalaydi
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # birinchi va oxirgi qatorni olib tashlaydi
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)


def call_ai(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> tuple[dict, str]:
    last_error = None
    client = get_client()

    for model in FALLBACK_MODELS:
        for attempt in range(5):  # 5 marta har bir model uchun urinish
            try:
                # Combine system and user prompts for Gemini
                full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
                
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                )
                
                content = response.text
                result = clean_json(content)
                logger.info(f"[AI] {model} ishlatildi (urinish {attempt + 1})")
                return result, model

            except json.JSONDecodeError as e:
                logger.error(f"[AI] {model} JSON parse xato: {e}\nContent: {content[:200]}")
                last_error = e

            except Exception as e:
                error_str = str(e)
                logger.error(f"[AI] {model} xatolik (urinish {attempt + 1}): {e}")
                last_error = e
                
                # 503 yoki 429 xatolik bo'lsa, kutib qayta urinamiz
                if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < 2:  # oxirgi urinish emas
                        # Google 429 uchun 11 soniya tavsiya qiladi
                        wait_time = 12 if "429" in error_str else (5 + attempt * 3)  # 5, 8, 11, 14, 17s
                        logger.info(f"[AI] {model} uchun {wait_time} soniya kutamiz...")
                        time.sleep(wait_time)
                        continue
                
                # Boshqa xatolik bo'lsa, keyingi modelga o'tamiz
                time.sleep(2)  # Model o'zgartirishda 2 soniya kutish
                break

    raise RuntimeError(
        f"Barcha modellar ishlamadi. Xatolik: {last_error}"
    )