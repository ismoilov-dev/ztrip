from rest_framework import serializers
from .models import Subscription
from django.utils import timezone
class SubscriptionSerializers(serializers.ModelSerializer):
    is_premium = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'is_active',
            'is_premium', 'started_at', 'expires_at',
        ]
        read_only_fields = ['id', 'is_active', 'started_at']

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Tugash sanasi hozirgi vaqtdan katta bo'lishi kerak."
            )
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
