from collections import defaultdict
from apps.events.models import UserEvent
from apps.movies.models import Movie


def calculate_recommendations(user_id):
    events = (
        UserEvent.objects
        .filter(user_id=user_id)
        .select_related('movie')
        .prefetch_related('movie__genres')
    )

    genre_scores = defaultdict(float)
    opened_movie_ids = set()

    for event in events:
        if event.movie_id:
            opened_movie_ids.add(event.movie_id)

        genres = list(event.movie.genres.all()) if event.movie_id else []

        if event.event_type == 'movie_open':
            for g in genres:
                genre_scores[g.id] += 1

        elif event.event_type == 'time_on_page' and event.value and event.value > 60:
            for g in genres:
                genre_scores[g.id] += 2

        elif event.event_type == 'trailer_play':
            for g in genres:
                genre_scores[g.id] += 3

        elif event.event_type == 'watchlist_add':
            for g in genres:
                genre_scores[g.id] += 5

        elif event.event_type == 'rating_set' and event.value is not None:
            if event.value >= 8:
                for g in genres:
                    genre_scores[g.id] += 8
            elif event.value <= 4:
                for g in genres:
                    genre_scores[g.id] -= 5

    top_genre_ids = sorted(genre_scores, key=genre_scores.__getitem__, reverse=True)[:3]

    if not top_genre_ids:
        return Movie.objects.prefetch_related('genres').order_by('-vote_average')[:10]

    movies = (
        Movie.objects
        .filter(genres__id__in=top_genre_ids)
        .exclude(id__in=opened_movie_ids)
        .prefetch_related('genres')
        .order_by('-vote_average')
        .distinct()[:10]
    )

    return movies
