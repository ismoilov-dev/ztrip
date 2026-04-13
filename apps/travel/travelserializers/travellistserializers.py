from rest_framework import serializers
# from apps.location.models import Location
from apps.travel.models import Travel
# from apps.location.serializers import LocationListSerializer


class TravelSerializer(serializers.ModelSerializer):
    total_days     = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )

    class Meta:
        model  = Travel
        fields = [
            'id', 'title',
            'start_date', 'end_date', 'total_days',
            'budget', 'status', 'status_display',
            'created_at',
        ]
        read_only_fields = ['id', 'total_days', 'created_at']

    def validate(self, attrs):
        start = attrs.get('start_date')
        end   = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': 'Tugash sanasi boshlanishdan oldin bo\'lishi mumkin emas.'}
            )
        return attrs

    def create(self, validated_data):
        # user JWT dan olinadi — frontenddan kelmaydi
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TravelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Travel
        fields = ['id', 'title', 'start_date', 'end_date', 'budget', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class TravelWriteSerializers(serializers.ModelSerializer):
    total_days = serializers.IntegerField(read_only=True)
    # ❌ budget = serializers.IntegerField() — olib tashlandi

    class Meta:
        model  = Travel
        fields = ['id', 'title', 'start_date', 'end_date', 'total_days', 'budget', 'status']
        read_only_fields = ['id']

    def validate(self, attrs):
        start = attrs.get('start_date')
        end   = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': 'Tugash sanasi boshlanishdan oldin bo\'lishi mumkin emas.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)