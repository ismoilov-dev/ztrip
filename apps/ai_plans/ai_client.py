import json
import logging
from openai import OpenAI, RateLimitError, APIStatusError

logger = logging.getLogger("ai_plans")

FALLBACK_MODELS = [
    "llama3.3-70b-instruct",
    "openai-gpt-oss-20b",
    "llama3-8b-instruct",
]


def get_client():
    from django.conf import settings
    return OpenAI(
        base_url=settings.MEGALLM_BASE_URL,
        api_key=settings.MEGALLM_API_KEY,
    )


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
            # llama uchun response_format ishlamaydi — olib tashlaymiz
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            result  = clean_json(content)
            logger.info(f"[AI] {model} ishlatildi")
            return result, model

        except json.JSONDecodeError as e:
            logger.error(f"[AI] {model} JSON parse xato: {e}\nContent: {content[:200]}")
            last_error = e

        except RateLimitError as e:
            logger.warning(f"[AI] {model} rate limit → keyingi model")
            last_error = e

        except APIStatusError as e:
            if e.status_code in [402, 429, 503]:
                logger.warning(f"[AI] {model} {e.status_code} → keyingi model")
                last_error = e
            else:
                logger.error(f"[AI] {model} xatolik: {e}")
                last_error = e

        except Exception as e:
            logger.error(f"[AI] {model} kutilmagan xato: {e}")
            last_error = e

    raise RuntimeError(
        f"Barcha modellar ishlamadi. Xatolik: {last_error}"
    )