from django.db import models
from django.contrib.auth.models import User
from apps.movies.models import Movie


class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='recommended_to')
    score = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.movie} → {self.user}: {self.score:.2f}'
