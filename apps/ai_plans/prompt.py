import json
from apps.location.models import Location

LANGUAGE_MAP = {
    "uz": "O'zbek tilida",
    "ru": "На русском языке",
    "en": "In English",
}


def get_locations(city: str, interests: list) -> list:
    qs = Location.objects.filter(city__icontains=city)
    if interests:
        qs = qs.filter(type__in=interests)
    if not qs.exists():
        qs = Location.objects.filter(city__icontains=city)
    if not qs.exists():
        qs = Location.objects.all()[:25]
    return [
        {
            "id": l.id,
            "name": l.name,
            "type": l.get_type_display(),
            "city": l.city,
            "price": float(l.price),
            "desc": (l.description or "")[:80],
        }
        for l in qs
    ]


# ═══════════════════════════════════════════════
# ROLE 1 — TRAVEL PLANNER
# ═══════════════════════════════════════════════
TRAVEL_PLANNER_SYSTEM = """Sen ZTrip sayohat rejalovchi assistantisan.
Foydalanuvchi bergan ma'lumotlar asosida kunlik marshrut tuzasan.

QOIDALAR:
1. FAQAT berilgan locations ID laridan foydalanasan
2. Bir kunda 3-5 ta location
3. Locationlarni geografik yaqinligiga qarab tartiblaysan
4. Faqat sof JSON qaytarasan — izoh, markdown YO'Q"""

TRAVEL_PLANNER_SCHEMA = {
    "days": [{
        "day": "<int>",
        "title": "<str>",
        "locations": [{
            "id": "<int>",
            "duration_min": "<int>",
            "best_time": "<str>",
            "tip": "<str>",
        }],
    }],
    "total_estimated_cost": "<int> UZS",
    "best_season": "<str>",
    "summary": "<str>",
    "tips": "<str>",
}

def travel_planner_prompt(city, days, budget, interests, language, locations):
    return f"""SHAHAR:{city} KUN:{days} BYUDJET:{f'{budget:,.0f} UZS' if budget else 'ochiq'}
QIZIQISHLAR:{', '.join(interests) or 'hammasi'} TIL:{LANGUAGE_MAP.get(language,'O\'zbek tilida')}

LOCATIONLAR:
{json.dumps(locations, ensure_ascii=False)}

FORMAT (aynan shu strukturada qaytarasan):
{json.dumps(TRAVEL_PLANNER_SCHEMA, ensure_ascii=False)}"""


# ═══════════════════════════════════════════════
# ROLE 2 — AUDIO GUIDE
# ═══════════════════════════════════════════════
AUDIO_GUIDE_SYSTEM = """Sen ZTrip audio gid skript yozuvchisan.
Berilgan joy haqida TTS uchun quloqqa yoqimli matn yozasan.

QOIDALAR:
1. 60-90 soniyalik audio (150-200 so'z)
2. "Siz hozir ... oldida turibsiz" kabi jonli til
3. 2-3 ta qiziqarli tarixiy fakt
4. Kirish narxi, ish vaqti, amaliy maslahat
5. Faqat sof JSON qaytarasan"""

AUDIO_GUIDE_SCHEMA = {
    "location_id": "<int>",
    "title": "<str>",
    "script": "<str> 150-200 so'z",
    "duration_sec": "<int>",
    "highlights": ["<str>"],
    "practical_info": {
        "open_hours": "<str>",
        "entry_fee": "<str>",
        "tip": "<str>",
    },
}

def audio_guide_prompt(location_id, name, loc_type, description, language):
    return f"""JOY:{name} TUR:{loc_type} TIL:{LANGUAGE_MAP.get(language,'O\'zbek tilida')}
TAVSIF:{(description or '')[:200]} LOCATION_ID:{location_id}

FORMAT:
{json.dumps(AUDIO_GUIDE_SCHEMA, ensure_ascii=False)}"""


# ═══════════════════════════════════════════════
# ROLE 3 — RECOMMENDER
# ═══════════════════════════════════════════════
RECOMMENDER_SYSTEM = """Sen ZTrip shaxsiy joy tavsiyachisan.
Foydalanuvchi qiziqishlari asosida yangi joylar tavsiya qilasan.

QOIDALAR:
1. Avval borilgan joylarni TAVSIYA QILMA
2. Har tavsiya uchun aniq sabab
3. must_see/hidden_gem/popular kategoriyalarga ajrat
4. Faqat sof JSON qaytarasan"""

RECOMMENDER_SCHEMA = {
    "recommendations": [{
        "location_id": "<int>",
        "score": "<float> 0.0-1.0",
        "reason": "<str>",
        "category": "must_see|hidden_gem|popular",
    }],
    "message": "<str>",
}

def recommender_prompt(interests, visited_ids, locations, language):
    return f"""QIZIQISHLAR:{', '.join(interests) or 'belgilanmagan'}
BORILGAN_IDlar:{visited_ids or 'yo\'q'} TIL:{LANGUAGE_MAP.get(language,'O\'zbek tilida')}

LOCATIONLAR:
{json.dumps(locations, ensure_ascii=False)}

FORMAT:
{json.dumps(RECOMMENDER_SCHEMA, ensure_ascii=False)}"""