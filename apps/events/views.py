import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.movies.models import Movie
from apps.movies.serializers import MovieListSerializer
from .models import UserEvent
from .serializers import UserEventSerializer

logger = logging.getLogger(__name__)


class EventBatchView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        events_data = request.data
        if not isinstance(events_data, list):
            return Response({'detail': 'Expected a list of events.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserEventSerializer(data=events_data, many=True)
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None
        to_create = []

        for item in serializer.validated_data:
            movie_id = item.get('movie_id')
            movie = None
            if movie_id:
                movie = Movie.objects.filter(id=movie_id).first()

            to_create.append(UserEvent(
                user=user,
                movie=movie,
                event_type=item['event_type'],
                value=item.get('value'),
            ))

        UserEvent.objects.bulk_create(to_create)
        logger.info('Saved %d events for user %s', len(to_create), user)
        return Response({'saved': len(to_create)}, status=status.HTTP_201_CREATED)


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seen_ids = []
        seen_set = set()
        events = (
            UserEvent.objects
            .filter(user=request.user, event_type='movie_open', movie__isnull=False)
            .select_related('movie')
            .order_by('-timestamp')
        )
        for e in events:
            if e.movie_id not in seen_set:
                seen_set.add(e.movie_id)
                seen_ids.append(e.movie_id)

        movies = {m.id: m for m in Movie.objects.filter(id__in=seen_ids).prefetch_related('genres')}
        ordered = [movies[mid] for mid in seen_ids if mid in movies]

        serializer = MovieListSerializer(ordered, many=True)
        return Response(serializer.data)
