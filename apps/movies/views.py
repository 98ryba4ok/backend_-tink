import logging
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Genre, Movie, UserRating, Comment
from .serializers import (
    GenreSerializer, MovieListSerializer, MovieDetailSerializer,
    CommentSerializer, UserRatingSerializer,
)

logger = logging.getLogger(__name__)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer

    def get_queryset(self):
        qs = Movie.objects.prefetch_related('genres')
        params = self.request.query_params

        genre = params.get('genre')
        if genre:
            qs = qs.filter(genres__id=genre)

        year = params.get('year')
        if year:
            qs = qs.filter(release_date__year=year)

        rating_min = params.get('rating_min')
        if rating_min:
            qs = qs.filter(vote_average__gte=rating_min)

        search = params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(overview__icontains=search))

        ordering = params.get('ordering', '-vote_average')
        allowed_orderings = ('vote_average', '-vote_average', 'release_date', '-release_date', 'title', '-title')
        if ordering in allowed_orderings:
            qs = qs.order_by(ordering)

        return qs

    @action(detail=False, methods=['get'])
    def trending(self, request):
        movies = Movie.objects.prefetch_related('genres').order_by('-vote_average')[:20]
        serializer = MovieListSerializer(movies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        movie = self.get_object()
        if request.method == 'GET':
            qs = Comment.objects.filter(movie=movie).select_related('user').order_by('-created_at')
            serializer = CommentSerializer(qs, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, movie=movie)
        logger.info('User %s commented on movie %s', request.user.id, movie.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        movie = self.get_object()
        serializer = UserRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating, created = UserRating.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'score': serializer.validated_data['score']},
        )
        logger.info('User %s rated movie %s: %s', request.user.id, movie.id, rating.score)
        return Response(UserRatingSerializer(rating).data, status=status.HTTP_200_OK)
