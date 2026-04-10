from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.subscriptions.models import Subscription


class PaymentStatus(models.TextChoices):
    PENDING   = "pending",   _("Pending")
    COMPLETED = "completed", _("Completed")
    FAILED    = "failed",    _("Failed")
    REFUNDED  = "refunded",  _("Refunded")


class PaymentProvider(models.TextChoices):
    STRIPE = "stripe", _("Stripe")
    PAYME  = "payme",  _("Payme")
    CLICK  = "click",  _("Click")


class Payment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("user"),
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("subscription"),
    )
    amount = models.DecimalField(
        _("amount"),
        max_digits=10,
        decimal_places=2,
    )
    currency = models.CharField(
        _("currency"),
        max_length=10,
        default="USD",
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    provider = models.CharField(
        _("provider"),
        max_length=30,
        choices=PaymentProvider.choices,
    )
    reference = models.CharField(
        _("provider reference"),
        max_length=200,
        blank=True,
        # Stripe payment_intent_id yoki Payme transaction id
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    class Meta:
        db_table = "payments"
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} | {self.amount} {self.currency} | {self.status}"

    def mark_completed(self):
        self.status = PaymentStatus.COMPLETED
        self.save(update_fields=["status"])
        if self.subscription:
            self.subscription.is_active = True
            self.subscription.save(update_fields=["is_active"])