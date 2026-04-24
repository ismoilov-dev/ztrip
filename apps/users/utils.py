import secrets
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

OTP_TTL = 300            # 5 daqiqa
OTP_RESEND_COOLDOWN = 60 # 1 daqiqa
OTP_MAX_ATTEMPTS = 5


def _otp_key(email):       return f"otp:code:{email.lower()}"
def _attempts_key(email):  return f"otp:attempts:{email.lower()}"
def _cooldown_key(email):  return f"otp:cooldown:{email.lower()}"


def _generate_code():
    # secrets — random dan ko‘ra xavfsizroq
    return f"{secrets.randbelow(10**6):06d}"


def send_otp(email: str):
    email = email.lower().strip()

    if cache.get(_cooldown_key(email)):
        return False, "Yangi kod so‘rashdan oldin biroz kuting."

    code = _generate_code()
    cache.set(_otp_key(email), code, OTP_TTL)
    cache.set(_cooldown_key(email), 1, OTP_RESEND_COOLDOWN)
    cache.delete(_attempts_key(email))

    send_mail(
        subject="Tasdiqlash kodi",
        message=f"Sizning kodingiz: {code}\nKod {OTP_TTL // 60} daqiqa amal qiladi.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return True, "Kod yuborildi."


def verify_otp(email: str, code: str):
    email = email.lower().strip()
    stored = cache.get(_otp_key(email))

    if not stored:
        return False, "Kod muddati tugagan yoki mavjud emas."

    attempts = cache.get(_attempts_key(email), 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        cache.delete(_otp_key(email))
        return False, "Urinishlar soni tugadi. Yangi kod so‘rang."

    if stored != code:
        cache.set(_attempts_key(email), attempts + 1, OTP_TTL)
        return False, "Kod noto‘g‘ri."

    cache.delete(_otp_key(email))
    cache.delete(_attempts_key(email))
    return True, "Tasdiqlandi."