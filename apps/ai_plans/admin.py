from django.contrib import admin
from .models import AIPlan
from unfold.admin import ModelAdmin
admin.site.register(AIPlan)
class AIplanClass(ModelAdmin):
    list_display = ('id', 'city', 'days', 'budget', 'interests', 'language', 'status', 'is_applied', 'travel', 'created_at')
