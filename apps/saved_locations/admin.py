from django.contrib import admin
from .models import SavedLocation
from unfold.admin import ModelAdmin

admin.site.register(SavedLocation)
class SavedLocationsAdmin(ModelAdmin):
    list_display = ['user', 'location']