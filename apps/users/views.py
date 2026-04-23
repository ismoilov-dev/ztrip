from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.users.models import User

from .serializers import GoogleAuthSerializer, UserSerializer, UserUpdateSerializer, LoginSerializers


def _jwt_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }

extend_schema(summary='Google auth')
class GoogleAuthView(GenericAPIView):
    permission_classes     = [AllowAny]
    authentication_classes = []
    serializer_class       = GoogleAuthSerializer

    @extend_schema(
        request=GoogleAuthSerializer,
        # security=[],
        responses={
            200: UserSerializer,
            201: UserSerializer,
            400: OpenApiResponse(description="Token yaroqsiz"),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, created = serializer.get_or_create_user()

        return Response(
            {
                "user":    UserSerializer(user).data,
                "tokens":  _jwt_tokens(user),
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserSerializer

    def get(self, request):
        return Response(self.get_serializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)
        
@extend_schema(tags=['auth'], summary='Email + avatar orqali login')
class LoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializers
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        avatar_url = serializer.validated_data.get('avatar_url') or 'https://example.com/default-avatar.png'

        # User bor bo'lsa topamiz, yo'q bo'lsa yaratamiz
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,        # agar username majburiy bo'lsa
                'avatar_url': avatar_url,
            }
        )

        # Mavjud user bo'lsa, avatar_url ni yangilaymiz (agar kelgan bo'lsa)
        if not created and serializer.validated_data.get('avatar_url'):
            user.avatar_url = avatar_url
            user.save(update_fields=['avatar_url'])


        return Response({
            "tokens": _jwt_tokens(user),
            # 'user': {
            #     'id': user.id,
            #     'email': user.email,
            #     'avatar_url': user.avatar_url,
            # }
        }, status=status.HTTP_200_OK)