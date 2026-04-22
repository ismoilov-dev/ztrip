import json
import logging
import google.genai as genai

logger = logging.getLogger("ai_plans")

FALLBACK_MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
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
        try:
            # Combine system and user prompts for Gemini
            full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
            
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=genai.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            content = response.text
            result = clean_json(content)
            logger.info(f"[AI] {model} ishlatildi")
            return result, model

        except json.JSONDecodeError as e:
            logger.error(f"[AI] {model} JSON parse xato: {e}\nContent: {content[:200]}")
            last_error = e

        except Exception as e:
            logger.error(f"[AI] {model} xatolik: {e}")
            last_error = e

    raise RuntimeError(
        f"Barcha modellar ishlamadi. Xatolik: {last_error}"
    )