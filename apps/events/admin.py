from django.contrib import admin
from .models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'movie', 'value', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('user__username', 'movie__title')
    readonly_fields = ('timestamp',)
