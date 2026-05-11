import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.movies.serializers import MovieListSerializer
from .engine import calculate_recommendations

logger = logging.getLogger(__name__)


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        movies = calculate_recommendations(request.user.id)
        serializer = MovieListSerializer(movies, many=True)
        logger.info('Recommendations requested by user %s', request.user.id)
        return Response(serializer.data)
