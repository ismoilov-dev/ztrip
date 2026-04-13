from django.contrib import admin
from .models import Travel, TravelLocation
from unfold.admin import ModelAdmin
admin.site.register(Travel)
class TravelAdmin(ModelAdmin):
    list_display = ('id', 'user', 'city', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'city')
    search_fields = ('user__email', 'city')

admin.site.register(TravelLocation)
class TravelLocationAdmin(ModelAdmin):
    list_display = ('travel', 'location', 'day_number', 'order')
    list_filter = ('day_number', 'order')
