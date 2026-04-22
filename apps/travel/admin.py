from django.contrib import admin
from .models import Travel, TravelLocation
from unfold.admin import ModelAdmin

@admin.register(Travel)
class TravelAdmin(ModelAdmin):
    list_display = ('id', 'user', 'title', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('user__email', 'title')

@admin.register(TravelLocation)
class TravelLocationAdmin(ModelAdmin):
    list_display = ('travel', 'location', 'visit_day', 'order_index')
    list_filter = ('visit_day', 'order_index')
