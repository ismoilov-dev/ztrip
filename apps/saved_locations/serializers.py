from rest_framework import serializers
from apps.location.serializers import LocationListSerializer
from .models import SavedLocation
from apps.location.models import Location


class SavedLocationSerializer(serializers.ModelSerializer):
    # read — to'liq location ma'lumoti
    location = LocationListSerializer(read_only=True)
    # write — faqat id yuboriladi
    location_id = serializers.PrimaryKeyRelatedField(
       queryset=Location.objects.all(),
       source='location',
       write_only=True,
)

    class Meta:
        model = SavedLocation
        fields = ['id', 'location', 'location_id', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # user JWT dan olinadi
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)