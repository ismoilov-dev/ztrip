# admin.py
from django.contrib import admin
from .models import Location
from unfold.admin import ModelAdmin

@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ['id', "name", "city", "type", "is_premium"]
    list_filter = ["type", "is_premium", "country"]
    search_fields = ["name", "city"]