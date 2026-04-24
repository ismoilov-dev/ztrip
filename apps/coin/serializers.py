from rest_framework import serializers
from .models import UserCoin


class UserCoinSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserCoin
        fields = ['user_id', 'xp', 'streak', 'rewards', 'created_at', 'updated_at']
        read_only_fields = ['user_id', 'created_at', 'updated_at']

class UserCoinUpdateSerializer(serializers.ModelSerializer):
    xp = serializers.IntegerField(required=False, default=0)
    streak = serializers.IntegerField(required=False, default=0)
    rewards = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )

    class Meta:
        model = UserCoin
        fields = ['xp', 'streak', 'rewards']

    def create(self, validated_data):
        return UserCoin.objects.create(**validated_data)