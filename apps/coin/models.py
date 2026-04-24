from django.db import models
from apps.users.models import User


class UserCoin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coin')
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    rewards = models.JSONField(default=list, blank=True)  # list of strings

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_coins'
        verbose_name = 'User Coin'
        verbose_name_plural = 'User Coins'

    def __str__(self):
        return f"{self.user_id} | XP: {self.xp} | Streak: {self.streak}"