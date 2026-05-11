from django.contrib import admin
from .models import Genre, Movie, UserRating, Comment


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'vote_average', 'release_date')
    search_fields = ('title',)
    list_filter = ('genres',)
    filter_horizontal = ('genres',)


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('user__username', 'movie__title')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'created_at')
    search_fields = ('user__username', 'movie__title', 'text')
