from rest_framework import serializers
from apps.location.models import Location
from .models import Travel, TravelLocation, TravelStatus
from apps.location.serializers import LocationListSerializer
from drf_spectacular.utils import extend_schema_field

class TravelLocationSerializer(serializers.ModelSerializer):
    # write — faqat id yuboriladi
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True,
    )
    # read — to'liq location ma'lumoti
    location = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = TravelLocation
        fields = [
            'id', 'travel',
            'location', 'location_id',
            'visit_day', 'order_index',
        ]
        read_only_fields = ['id', 'travel', 'location']

    def get_location(self, obj):
        return LocationListSerializer(obj.location).data

    def validate_visit_day(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'visit_day 1 dan kichik bo\'lishi mumkin emas.'
            )
        return value

    def validate(self, attrs):
        # travel context dan keladi
        travel = self.context.get('travel')
        if travel and attrs.get('visit_day'):
            if attrs['visit_day'] > travel.total_days:
                raise serializers.ValidationError({
                    'visit_day': f'Maksimal {travel.total_days} kun.'
                })
        return attrs

class TravelDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_days     = serializers.IntegerField(read_only=True)
    locations      = serializers.SerializerMethodField()

    class Meta:
        model  = Travel
        fields = [
            "id", "title", "status", "status_display",
            "start_date", "end_date", "total_days",
            "budget", "locations", "created_at",
        ]
    @extend_schema_field(serializers.DictField())
    def get_locations(self, obj):
        days = {}
        for tl in obj.travel_locations.select_related("location").order_by("visit_day", "order_index"):
            key = f"day_{tl.visit_day}"
            if key not in days:
                days[key] = []
            days[key].append({
                "id":    tl.location.id,
                "name":  tl.location.name,
                "city":  tl.location.city,
                "image": tl.location.image.url if tl.location.image else None,
            })
        return days