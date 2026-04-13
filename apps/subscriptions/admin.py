from django.contrib import admin
from .models import Subscription
from unfold.admin import ModelAdmin

admin.site.register(Subscription)
class SubscriptionsAdmin(ModelAdmin):
  list_display=['user', 'plan', 'is_active', 'started_at', 'expires_at']