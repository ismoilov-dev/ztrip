from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.users.models import User

from .serializers import GoogleAuthSerializer, UserSerializer, UserUpdateSerializer, LoginSerializers, RequestOTPSerializer, VerifyOTPSerializer
from .models import User
from .utils import send_otp, verify_otp

def _jwt_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        # "refresh": str(refresh),
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

class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RequestOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP yuborildi"),
            429: OpenApiResponse(description="Juda ko'p so'rov"),
        },
    )
    def post(self, request):
        s = RequestOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        ok, msg = send_otp(s.validated_data["email"])
        return Response(
            {"detail": msg},
            status=status.HTTP_200_OK if ok else status.HTTP_429_TOO_MANY_REQUESTS,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP muvaffaqiyatli tasdiqlandi"),
            400: OpenApiResponse(description="Noto'g'ri email yoki kod"),
        },
    )
    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"]
        code = s.validated_data["code"]

        ok, msg = verify_otp(email, code)
        if not ok:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "detail": msg,
            "is_new_user": created or user.is_new_user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)