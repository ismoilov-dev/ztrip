from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PlanType(models.TextChoices):
    FREE    = "free",    _("Free")
    MONTHLY = "monthly", _("Monthly")
    YEARLY  = "yearly",  _("Yearly")


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name=_("user"),
    )
    plan = models.CharField(
        _("plan"),
        max_length=20,
        choices=PlanType.choices,
        default=PlanType.FREE,
    )
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        db_index=True,
    )
    started_at = models.DateTimeField(
        _("started at"),
        auto_now_add=True,
    )
    expires_at = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        # Free plan uchun null (muddatsiz)
    )

    class Meta:
        db_table = "subscriptions"
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} — {self.plan}"

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])