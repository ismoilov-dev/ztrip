from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AIPlanStatus(models.TextChoices):
    PENDING   = "pending",   _("Pending")
    COMPLETED = "completed", _("Completed")
    FAILED    = "failed",    _("Failed")
    APPLIED   = "applied",   _("Applied")


class AIPlan(models.Model):
    """
    plan_json strukturasi:
    {
      "days": [
        {
          "day": 1,
          "title": "Tarixiy Samarqand",
          "locations": [
            {
              "id": 3,
              "duration_min": 90,
              "best_time": "09:00",
              "tip": "Erta keling"
            }
          ]
        }
      ],
      "total_estimated_cost": 250000,
      "best_season": "Bahor",
      "summary": "...",
      "tips": "..."
    }
    """

    # ── Kimniki ───────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_plans",
        verbose_name=_("user"),
    )

    # ── Travel bog'lanishi (apply dan keyin) ──────────────────
    travel = models.OneToOneField(
        "travel.Travel",          # string → circular import yo'q
        on_delete=models.SET_NULL,  # travel o'chsa plan qoladi
        related_name="ai_plan",
        verbose_name=_("travel"),
        null=True,                 # generate da travel yo'q
        blank=True,
    )

    # ── Shahar — erkin yoziladi ───────────────────────────────
    # "Samarqand", "Xiva", "Toshkent" yoki "Paris"
    # AI shu shahar bo'yicha DB dan location qidiradi
    city = models.CharField(
        _("city"),
        max_length=100,
        db_index=True,
    )
    days = models.PositiveSmallIntegerField(
        _("number of days"),
    )
    budget = models.DecimalField(
        _("budget"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    interests = models.JSONField(
        _("interests"),
        default=list,
        blank=True,
        # ["historical", "museum", "nature"]
    )
    language = models.CharField(
        _("language"),
        max_length=5,
        default="uz",
    )

    # ── AI natijasi ───────────────────────────────────────────
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=AIPlanStatus.choices,
        default=AIPlanStatus.PENDING,
        db_index=True,
    )
    plan_json = models.JSONField(
        _("plan data"),
        default=dict,
        blank=True,
    )
    ai_model_used = models.CharField(
        _("AI model used"),
        max_length=50,
        blank=True,
        # qaysi model ishlatilganini saqlaydi: "gemini-2.5-flash"
    )
    prompt_used = models.TextField(
        _("prompt used"),
        blank=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    class Meta:
        db_table = "ai_plans"
        verbose_name = _("AI plan")
        verbose_name_plural = _("AI plans")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return f"AI Plan — {self.city} {self.days} kun ({self.user})"

    @property
    def is_applied(self):
        return self.status == AIPlanStatus.APPLIED