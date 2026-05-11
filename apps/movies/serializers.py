from rest_framework import serializers
from .models import Genre, Movie, UserRating, Comment


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'tmdb_id')


class MovieListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ('id', 'tmdb_id', 'title', 'overview', 'poster_path', 'vote_average', 'release_date', 'genres')


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    user_rating = serializers.SerializerMethodField()
    our_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            'id', 'tmdb_id', 'title', 'overview', 'poster_path',
            'youtube_key', 'vote_average', 'release_date', 'runtime',
            'genres', 'user_rating', 'our_rating',
        )

    def get_user_rating(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        rating = obj.ratings.filter(user=request.user).first()
        return rating.score if rating else None

    def get_our_rating(self, obj):
        from django.db.models import Avg
        result = obj.ratings.aggregate(avg=Avg('score'))
        avg = result['avg']
        return round(avg, 1) if avg is not None else None


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'username', 'text', 'created_at')
        read_only_fields = ('id', 'username', 'created_at')


class UserRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = ('id', 'score', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_score(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError('Score must be between 1 and 10.')
        return value
