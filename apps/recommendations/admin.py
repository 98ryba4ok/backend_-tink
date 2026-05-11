from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'updated_at')
    search_fields = ('user__username', 'movie__title')
    readonly_fields = ('updated_at',)
