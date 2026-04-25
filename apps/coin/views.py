from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from apps.users.models import User
from .models import UserCoin
from .serializers import UserCoinSerializer, UserCoinUpdateSerializer


class UserCoinView(APIView):
    serializer_class = UserCoinUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            coin, created = UserCoin.objects.get_or_create(user=user)
            return coin
        except User.DoesNotExist:
            return None

    # GET /coin/<user_id>/
    @swagger_auto_schema(responses={200: UserCoinSerializer})
    def get(self, request, user_id):
        coin = self.get_object(user_id)
        if coin is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserCoinSerializer(coin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /coin/<user_id>/
    @swagger_auto_schema(
        request_body=UserCoinUpdateSerializer,
        responses={201: UserCoinSerializer},
        operation_description="Create user coin data with xp, streak, and rewards",
        examples={
            'application/json': {
                'xp': 100,
                'streak': 5,
                'rewards': ['badge_1']
            }
        }
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if UserCoin.objects.filter(user=user).exists():
            return Response({'detail': 'Already exists. Use PATCH.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserCoinUpdateSerializer(data=request.data)
        if serializer.is_valid():
            coin = serializer.save(user=user)
            return Response(UserCoinSerializer(coin).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PATCH /coin/<user_id>/
    @swagger_auto_schema(
        request_body=UserCoinUpdateSerializer,
        responses={200: UserCoinSerializer},
        operation_description="Update user coin data (partial update)",
        examples={
            'application/json': {
                'xp': 100,
                'streak': 5,
                'rewards': ['badge_1']
            }
        }
    )
    def patch(self, request, user_id):
        coin = self.get_object(user_id)
        if coin is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserCoinUpdateSerializer(coin, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserCoinSerializer(coin).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE /coin/<user_id>/
    @swagger_auto_schema(responses={204: 'Deleted successfully.'})
    def delete(self, request, user_id):
        coin = self.get_object(user_id)
        if coin is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        coin.delete()
        return Response({'detail': 'Deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)