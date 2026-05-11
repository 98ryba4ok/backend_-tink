from rest_framework import serializers
from django.contrib.auth.models import User
from apps.movies.models import Movie
from apps.movies.serializers import MovieListSerializer
from apps.users.models import Watchlist


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')


class WatchlistSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),
        source='movie',
        write_only=True,
    )

    class Meta:
        model = Watchlist
        fields = ('id', 'movie', 'movie_id', 'added_at')
        read_only_fields = ('id', 'added_at')
