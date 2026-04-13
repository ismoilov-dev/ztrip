from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.location.models import Location


class TravelStatus(models.TextChoices):
    DRAFT     = "draft",     _("Draft")
    ACTIVE    = "active",    _("Active")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")


class Travel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="travels",
        verbose_name=_("user"),
    )
    title = models.CharField(
        _("title"),
        max_length=200,
    )
    start_date = models.DateField(
        _("start date"),
    )
    end_date = models.DateField(
        _("end date"),
    )
    budget = models.DecimalField(
        _("budget"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=TravelStatus.choices,
        default=TravelStatus.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    class Meta:
        db_table = "travels"
        verbose_name = _("travel")
        verbose_name_plural = _("travels")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user})"

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1


class TravelLocation(models.Model):
    """Travel va Location o'rtasidagi ko'prikchi jadval.
    order_index: bir kun ichidagi tartib
    visit_day:   necha-kunchi kuni boriladi (1-dan boshlab)
    """
    travel = models.ForeignKey(
        Travel,
        on_delete=models.CASCADE,
        related_name="travel_locations",
        verbose_name=_("travel"),
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="travel_locations",
        verbose_name=_("location"),
    )
    visit_day = models.PositiveSmallIntegerField(
        _("visit day"),
        default=1,
        # 1 = birinchi kun, 2 = ikkinchi kun ...
    )
    order_index = models.PositiveSmallIntegerField(
        _("order index"),
        default=0,
        # o'sha kun ichidagi tartib
    )


    class Meta:
        db_table = "travel_locations"
        verbose_name = _("travel location")
        verbose_name_plural = _("travel locations")
        ordering = ["visit_day", "order_index"]
        unique_together = [("travel", "location")]
        # bir sayohatda bir location bir martdan

    def __str__(self):
        return f"Day {self.visit_day} — {self.location.name}"