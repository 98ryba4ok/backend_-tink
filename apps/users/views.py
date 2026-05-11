import logging
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Watchlist
from .serializers import RegisterSerializer, UserSerializer, WatchlistSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info('New user registered: %s', user.username)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'detail': 'Email и пароль обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Неверный email или пароль.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.MultipleObjectsReturned:
            return Response({'detail': 'Несколько аккаунтов с таким email. Обратитесь в поддержку.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response({'detail': 'Неверный email или пароль.'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        logger.info('User logged in: %s', user.username)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user).select_related('movie').prefetch_related('movie__genres')

    def perform_create(self, serializer):
        from django.db import IntegrityError
        try:
            serializer.save(user=self.request.user)
            logger.info('User %s added movie %s to watchlist', self.request.user.id, serializer.instance.movie_id)
        except IntegrityError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Фильм уже в избранном.'})
