from django.db import models
from django.contrib.auth.models import User
from apps.movies.models import Movie


class UserEvent(models.Model):
    EVENT_TYPES = [
        ('movie_open', 'Movie Open'),
        ('time_on_page', 'Time on Page'),
        ('trailer_play', 'Trailer Play'),
        ('watchlist_add', 'Watchlist Add'),
        ('watchlist_remove', 'Watchlist Remove'),
        ('rating_set', 'Rating Set'),
        ('comment_add', 'Comment Add'),
        ('search_query', 'Search Query'),
        ('filter_apply', 'Filter Apply'),
        ('recommendation_click', 'Recommendation Click'),
        ('bot_message_sent', 'Bot Message Sent'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    movie = models.ForeignKey(Movie, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    value = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.event_type} by {self.user} at {self.timestamp}'
