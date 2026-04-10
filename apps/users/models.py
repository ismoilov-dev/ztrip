from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email kiritish majburiy"))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser uchun is_staff=True bo'lishi shart"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser uchun is_superuser=True bo'lishi shart"))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    full_name = models.CharField(
        _("full name"),
        max_length=250,
        blank=True,
    )
    email = models.EmailField(
        _("email"),
        max_length=254,
        unique=True,
        db_index=True,
        error_messages={
            "unique": _("Bu email allaqachon ro'yxatdan o'tgan."),
        },
    )
    language_code = models.CharField(
        _("language"),
        max_length=10,
        default="en",
        choices=[
            ("en", "English"),
            ("ru", "Русский"),
            ("ar", "العربية"),
        ],
    )
    avatar_url = models.URLField(
        _("avatar URL"),
        max_length=500,
        blank=True,
    )
    country = models.CharField(
        _("country"),
        max_length=250,
        blank=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )
    is_new_user = models.BooleanField(default=True)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name or self.email