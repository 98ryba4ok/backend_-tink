from rest_framework import serializers
from apps.movies.serializers import MovieListSerializer
from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = ('id', 'movie', 'score', 'updated_at')
