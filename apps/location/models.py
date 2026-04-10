from django.db import models
from django.utils.translation import gettext_lazy as _


class LocationType(models.TextChoices):
    MUSEUM        = "museum",        _("Museum")
    PARK          = "park",          _("Park")
    RESTAURANT    = "restaurant",    _("Restaurant")
    HISTORICAL    = "historical",    _("Historical")
    ENTERTAINMENT = "entertainment", _("Entertainment")
    NATURE        = "nature",        _("Nature")
    OTHER         = "other",         _("Other")


class Location(models.Model):
    name        = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)

    image = models.ImageField(
        _("image"),
        upload_to="locations/images/%Y/%m/",
        blank=True,
        null=True,
    )
    audio = models.FileField(
        _("audio"),
        upload_to="locations/audio/%Y/%m/",
        blank=True,
        null=True,
    )
    price      = models.DecimalField(_("price"), max_digits=10, decimal_places=2, default=0)
    country    = models.CharField(_("country"), max_length=100, db_index=True)
    city       = models.CharField(_("city"), max_length=100, db_index=True)
    latitude   = models.FloatField(_("latitude"))
    longitude  = models.FloatField(_("longitude"))
    type       = models.CharField(_("type"), max_length=50, choices=LocationType.choices, default=LocationType.OTHER, db_index=True)
    is_premium = models.BooleanField(_("premium only"), default=False, db_index=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        db_table = "locations"
        verbose_name = _("location")
        verbose_name_plural = _("locations")
        ordering = ["country", "city", "name"]
        indexes = [
            models.Index(fields=["city", "type"]),
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["is_premium", "type"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.city}"