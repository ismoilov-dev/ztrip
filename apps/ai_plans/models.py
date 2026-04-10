from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.travel.models import Travel


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
          "locations": [
            {"name": "...", "lat": ..., "lng": ..., "duration_min": 60}
          ]
        }
      ],
      "tips": "...",
      "estimated_cost": 150.0
    }
    """
    travel = models.OneToOneField(
        Travel,
        on_delete=models.CASCADE,
        related_name="ai_plan",
        verbose_name=_("travel"),
    )
    city = models.CharField(
        _("city"),
        max_length=100,
    )
    days = models.PositiveSmallIntegerField(
        _("number of days"),
    )
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
    prompt_used = models.TextField(
        _("prompt used"),
        blank=True,
        # debug uchun OpenAI ga yuborilgan prompt
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

    def __str__(self):
        return f"AI Plan — {self.city} {self.days} kun"