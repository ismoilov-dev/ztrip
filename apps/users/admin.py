from django.contrib import admin
from .models import User
from unfold.admin import ModelAdmin

@admin.register(User)
class UserAdmin(ModelAdmin):
  list_display = ['email', 'is_premium']