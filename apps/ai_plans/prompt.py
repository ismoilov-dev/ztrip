import json
from apps.location.models import Location

LANGUAGE_MAP = {
    "uz": "O'zbek tilida",
    "ru": "На русском языке",
    "en": "In English",
}


def get_locations(city: str, interests: list) -> list:
    general_words = ["uzbekistan", "o'zbekiston", "узбекистан", "all", ""]
    
    if city.lower().strip() in general_words:
        qs = Location.objects.all()
    else:
        qs = Location.objects.filter(city__icontains=city)
        if not qs.exists():
            qs = Location.objects.all()

    # Interests bo'yicha filter
    if interests:
        filtered = qs.filter(type__in=interests)
        if filtered.exists():
            qs = filtered

    # Faqat eng kerakli fieldlar — token tejash
    return [
        {
            "id":   l.id,
            "name": l.name,
            "type": l.get_type_display(),
            "city": l.city,
        }
        for l in qs[:10]  # max 10 ta
    ]

# ═══════════════════════════════════════════════
# ROLE 1 — TRAVEL PLANNER
# ═══════════════════════════════════════════════
TRAVEL_PLANNER_SYSTEM = """Sen ZTrip sayohat rejalovchi assistantisan.
Foydalanuvchi bergan ma'lumotlar asosida kunlik marshrut tuzasan.

QOIDALAR:
1. FAQAT berilgan locations ID laridan foydalanasan
2. Bir kunda 2-4 ta location
3. Faqat sof JSON qaytarasan — izoh, markdown YO'Q"""


def travel_planner_prompt(city, days, budget, interests, language, locations):
    lang = LANGUAGE_MAP.get(language, "O'zbek tilida")
    
    # Dinamik kun schema
    days_schema = ",\n    ".join([
        f'{{"day": {i}, "title": "kun sarlavhasi", "locations": [{{"id": 1, "duration_min": 60, "tip": "maslahat"}}]}}'
        for i in range(1, days + 1)
    ])
    
    return f"""{lang} javob ber.

SHAHAR: {city}
KUNLAR: {days}
BYUDJET: {f'{budget:,.0f} UZS' if budget else 'ochiq'}
QIZIQISHLAR: {', '.join(interests) if interests else 'hammasi'}

FAQAT quyidagi locationlardan foydalanib plan tuz:
{json.dumps(locations, ensure_ascii=False)}

MUHIM: Aynan {days} ta kun bo'lishi SHART!

JSON formatida qaytar (boshqa hech narsa yozma):
{{
  "days": [
    {days_schema}
  ],
  "total_cost": "narx UZS",
  "summary": "qisqa xulosa"
}}"""


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


def audio_guide_prompt(location_id, name, loc_type, description, language):
    lang = LANGUAGE_MAP.get(language, "O'zbek tilida")
    return f"""{lang} javob ber.

JOY: {name}
TUR: {loc_type}
TAVSIF: {(description or '')[:200]}
LOCATION_ID: {location_id}

JSON formatida qaytar:
{{
  "location_id": {location_id},
  "title": "joy nomi",
  "script": "150-200 so'zlik audio matn",
  "duration_sec": 75,
  "highlights": ["fakt 1", "fakt 2"],
  "practical_info": {{
    "open_hours": "9:00-18:00",
    "entry_fee": "bepul yoki narxi",
    "tip": "amaliy maslahat"
  }}
}}"""


# ═══════════════════════════════════════════════
# ROLE 3 — RECOMMENDER
# ═══════════════════════════════════════════════
RECOMMENDER_SYSTEM = """Sen ZTrip shaxsiy joy tavsiyachisan.
Foydalanuvchi qiziqishlari asosida yangi joylar tavsiya qilasan.

QOIDALAR:
1. Avval borilgan joylarni TAVSIYA QILMA
2. Har tavsiya uchun aniq sabab
3. Faqat sof JSON qaytarasan"""


def recommender_prompt(interests, visited_ids, locations, language):
    lang = LANGUAGE_MAP.get(language, "O'zbek tilida")
    return f"""{lang} javob ber.

QIZIQISHLAR: {', '.join(interests) if interests else 'belgilanmagan'}
BORILGAN IDlar: {visited_ids or 'yo\'q'}

LOCATIONLAR:
{json.dumps(locations, ensure_ascii=False)}

JSON formatida qaytar:
{{
  "recommendations": [
    {{
      "location_id": 1,
      "score": 0.9,
      "reason": "sabab",
      "category": "must_see"
    }}
  ],
  "message": "umumiy xabar"
}}"""