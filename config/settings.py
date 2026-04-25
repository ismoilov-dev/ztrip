import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import config

# ===========================================================
# BASE
# ===========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG      = config("DEBUG", default=False, cast=bool)
USE_HTTPS  = config("USE_HTTPS", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [h.strip() for h in v.split(",")],
)

SITE_ID         = 1
AUTH_USER_MODEL = "users.User"

# ===========================================================
# SECURITY & PROXY (Nginx orqali ishlash uchun)
# ===========================================================
# Nginx orqali kelgan HTTPS so'rovlarni to'g'ri aniqlash
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000",
    cast=lambda v: [o.strip() for o in v.split(",")]
)

# ===========================================================
# APPLICATIONS
# ===========================================================
INSTALLED_APPS = [
    # ── unfold admin ──────────────────────────────────────
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",

    # ── django core ───────────────────────────────────────
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # ── third-party ───────────────────────────────────────
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "channels",
    "django_filters",
    "storages",

    # ── allauth ───────────────────────────────────────────
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # ── dj-rest-auth ──────────────────────────────────────
    "dj_rest_auth",
    "dj_rest_auth.registration",

    # ── local ─────────────────────────────────────────────
    "apps.users",
    "apps.location",
    'apps.travel',
    'apps.ai_plans',
    'apps.saved_locations',
    'apps.subscriptions',
    'apps.coin',
]

# ===========================================================
# MIDDLEWARE
# ===========================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# ===========================================================
# URLS / TEMPLATES / WSGI / ASGI
# ===========================================================
ROOT_URLCONF      = "config.urls"
WSGI_APPLICATION  = "config.wsgi.application"
ASGI_APPLICATION  = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ===========================================================
# DATABASE
# ===========================================================
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===========================================================
# AUTHENTICATION
# ===========================================================
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===========================================================
# ALLAUTH
# ===========================================================
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_UNIQUE_EMAIL               = True
ACCOUNT_LOGIN_METHODS              = {"email"}
ACCOUNT_SIGNUP_FIELDS              = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION         = config("ACCOUNT_EMAIL_VERIFICATION", default="none")

# ===========================================================
# GOOGLE OAUTH 2.0
# ===========================================================
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "APP": {
            "client_id": config("GOOGLE_CLIENT_ID"),
            "secret":    config("GOOGLE_CLIENT_SECRET"),
        },
    },
}

GOOGLE_CALLBACK_URL = config(
    "GOOGLE_CALLBACK_URL",
    default="http://localhost:8000/api/auth/social/google/callback/",
)

# ===========================================================
# DJ-REST-AUTH
# ===========================================================
REST_AUTH = {
    "USE_JWT":                   True,
    "JWT_AUTH_COOKIE":           "access_token",
    "JWT_AUTH_REFRESH_COOKIE":   "refresh_token",
    "JWT_AUTH_HTTPONLY":         True,
    "TOKEN_MODEL":               None,
    "USER_DETAILS_SERIALIZER":   "apps.users.serializers.UserSerializer",
}

# ===========================================================
# SIMPLE JWT
# ===========================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=config("JWT_ACCESS_LIFETIME_MINUTES", default=30, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("JWT_REFRESH_LIFETIME_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES":      ("Bearer",),
}

# ===========================================================
# REST FRAMEWORK
# ===========================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("THROTTLE_ANON", default="100/day"),
        "user": config("THROTTLE_USER", default="1000/day"),
    },
    "DEFAULT_RENDERER_CLASSES": (
        [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ]
        if DEBUG
        else ["rest_framework.renderers.JSONRenderer"]
    ),
}

# ===========================================================
# DRF SPECTACULAR (Swagger)
# ===========================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "Z Trip API",
    "DESCRIPTION": "Travel application API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "TravelStatusEnum": "apps.travel.models.TravelStatus",
        "AIPlanStatusEnum": "apps.ai_plans.models.AIPlanStatus",
        "LocationTypeEnum": "apps.location.models.LocationType",
    },
}

# ===========================================================
# CORS
# ===========================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ===========================================================
# INTERNATIONALIZATION
# ===========================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "UTC"
USE_I18N      = True
USE_TZ        = True

# ===========================================================
# STATIC FILES
# ===========================================================
STATIC_URL  = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ===========================================================
# MINIO (Media Storage)
PROTOCOL_SCHEME = "https" if USE_HTTPS else "http"

AWS_ACCESS_KEY_ID       = config("MINIO_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY   = config("MINIO_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET")
AWS_S3_ENDPOINT_URL     = f"{PROTOCOL_SCHEME}://{config('MINIO_ENDPOINT')}"
# ❌ AWS_S3_CUSTOM_DOMAIN = config("MINIO_ENDPOINT")  # ← O'CHIRING, SSL xatosi shu!
AWS_DEFAULT_ACL         = "public-read"
AWS_S3_FILE_OVERWRITE   = False
AWS_QUERYSTRING_AUTH    = False
AWS_S3_VERIFY           = False

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = f"{PROTOCOL_SCHEME}://{config('MINIO_ENDPOINT')}/{config('MINIO_BUCKET')}/"

# ===========================================================
# AI AUDIO GUIDE
# ===========================================================
AI_PROVIDER = config("AI_PROVIDER", default="gemini")

# Gemini API
GEMINI_API_KEY = config("GEMINI_API_KEY")
GEMINI_BASE_URL = config("GEMINI_BASE_URL", default="https://generativelanguage.googleapis.com/v1beta/openai")

# OpenAI
OPENAI_API_KEY = config("OPENAI_API_KEY", default=None)

# ElevenLabs
ELEVENLABS_API_KEY  = config("ELEVENLABS_API_KEY",  default=None)
ELEVENLABS_VOICE_ID = config("ELEVENLABS_VOICE_ID", default="21m00Tcm4TlvDq8ikWAM")

# ===========================================================
# CELERY & CHANNELS (Redis)
# ===========================================================
CELERY_BROKER_URL                         = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND                     = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT                     = ["json"]
CELERY_TASK_SERIALIZER                    = "json"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CACHES = {
    "default": {
        "BACKEND":  "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [config("REDIS_URL")]},
    }
}

# email backend
EMAIL_BACKEND       = config("EMAIL_BACKEND")
EMAIL_HOST          = config("EMAIL_HOST")
EMAIL_PORT          = config("EMAIL_PORT", cast=int)
EMAIL_USE_TLS       = config("EMAIL_USE_TLS", cast=bool)
EMAIL_HOST_USER     = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL  = config("DEFAULT_FROM_EMAIL")