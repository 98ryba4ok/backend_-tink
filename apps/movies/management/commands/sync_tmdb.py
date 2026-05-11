import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.movies.models import Movie, Genre

logger = logging.getLogger(__name__)

TMDB_BASE = 'https://api.themoviedb.org/3'
MIN_VOTE_COUNT = 100


class Command(BaseCommand):
    help = 'Sync movies from TMDB API (only quality: trailer + poster + 100+ votes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages', type=int, default=20,
            help='Pages to scan (20 movies/page). Default 20 = ~400 candidates → ~300 saved'
        )
        parser.add_argument(
            '--skip-existing', action='store_true',
            help='Skip movies already in DB (fast re-run)'
        )

    def handle(self, *args, **options):
        api_key = settings.TMDB_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR('TMDB_API_KEY is not set'))
            return

        pages = options['pages']
        skip_existing = options['skip_existing']
        created_count = 0
        skipped_count = 0

        genre_map = self._fetch_genre_map(api_key)
        self.stdout.write(f'Loaded {len(genre_map)} genres from TMDB')

        for page in range(1, pages + 1):
            self.stdout.write(f'Page {page}/{pages}...', ending=' ')
            movies_data = self._fetch_popular(api_key, page)
            if not movies_data:
                break

            for item in movies_data:
                # Skip: no poster
                if not item.get('poster_path'):
                    skipped_count += 1
                    continue

                # Skip: not enough votes (fake/unreliable rating)
                if item.get('vote_count', 0) < MIN_VOTE_COUNT:
                    skipped_count += 1
                    continue

                # Skip: already in DB (on re-runs)
                if skip_existing and Movie.objects.filter(tmdb_id=item['id']).exists():
                    skipped_count += 1
                    continue

                youtube_key = self._fetch_trailer_key(api_key, item['id'])

                # Skip: no trailer at all
                if not youtube_key:
                    skipped_count += 1
                    continue

                self._upsert_movie(item, youtube_key, genre_map)
                created_count += 1

            self.stdout.write(f'saved so far: {created_count}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Saved: {created_count}, Skipped (no poster/votes/trailer): {skipped_count}'
        ))

    def _fetch_genre_map(self, api_key):
        try:
            response = requests.get(
                f'{TMDB_BASE}/genre/movie/list',
                params={'api_key': api_key, 'language': 'ru-RU'},
                timeout=10,
            )
            response.raise_for_status()
            return {g['id']: g['name'] for g in response.json().get('genres', [])}
        except requests.RequestException as exc:
            logger.error('Failed to fetch genre list: %s', exc)
            return {}

    def _fetch_popular(self, api_key, page):
        try:
            response = requests.get(
                f'{TMDB_BASE}/movie/popular',
                params={'api_key': api_key, 'page': page, 'language': 'ru-RU'},
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException as exc:
            logger.error('Failed to fetch TMDB popular page %d: %s', page, exc)
            return []

    def _fetch_trailer_key(self, api_key, tmdb_id):
        """Russian trailer first, English fallback."""
        for lang in ('ru-RU', 'en-US'):
            try:
                response = requests.get(
                    f'{TMDB_BASE}/movie/{tmdb_id}/videos',
                    params={'api_key': api_key, 'language': lang},
                    timeout=10,
                )
                response.raise_for_status()
                for video in response.json().get('results', []):
                    if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                        return video['key']
            except requests.RequestException as exc:
                logger.warning('Videos fetch failed tmdb_id=%d lang=%s: %s', tmdb_id, lang, exc)
        return ''

    def _upsert_movie(self, data, youtube_key, genre_map):
        release_date = data.get('release_date') or None
        if release_date == '':
            release_date = None

        movie, _ = Movie.objects.update_or_create(
            tmdb_id=data['id'],
            defaults={
                'title': data.get('title', ''),
                'overview': data.get('overview', ''),
                'poster_path': data.get('poster_path', '') or '',
                'youtube_key': youtube_key,
                'vote_average': data.get('vote_average', 0),
                'release_date': release_date,
            },
        )

        genre_ids = []
        for tmdb_genre_id in data.get('genre_ids', []):
            genre, _ = Genre.objects.get_or_create(
                tmdb_id=tmdb_genre_id,
                defaults={'name': genre_map.get(tmdb_genre_id, str(tmdb_genre_id))},
            )
            genre_ids.append(genre.id)

        movie.genres.set(genre_ids)
