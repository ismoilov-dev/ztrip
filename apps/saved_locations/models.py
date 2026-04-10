from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.location.models import Location


class SavedLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_locations",
        verbose_name=_("user"),
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="saved_by",
        verbose_name=_("location"),
    )
    created_at = models.DateTimeField(
        _("saved at"),
        auto_now_add=True,
    )

    class Meta:
        db_table = "saved_locations"
        verbose_name = _("saved location")
        verbose_name_plural = _("saved locations")
        unique_together = [("user", "location")]
        # bir user bir locationni faqat bir marta saqlaydi
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.location.name}"