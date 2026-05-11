from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from apps.users.views import RegisterView, LoginView, MeView, WatchlistViewSet
from apps.movies.views import MovieViewSet, GenreViewSet
from apps.events.views import EventBatchView, HistoryView
from apps.recommendations.views import RecommendationsView

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', MeView.as_view(), name='me'),
    path('api/', include(router.urls)),
    path('api/events/', EventBatchView.as_view(), name='events'),
    path('api/history/', HistoryView.as_view(), name='history'),
    path('api/recommendations/', RecommendationsView.as_view(), name='recommendations'),
]
