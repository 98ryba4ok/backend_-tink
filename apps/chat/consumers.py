import json
import logging
import uuid
import requests
from collections import defaultdict
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

GIGACHAT_API_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'
GIGACHAT_OAUTH_URL = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info('WS connected: user=%s', self.scope['user'])

    async def disconnect(self, close_code):
        logger.info('WS disconnected: user=%s code=%s', self.scope['user'], close_code)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'error': 'Invalid JSON'}))
            return

        user_message = data.get('content', '').strip()
        if not user_message:
            await self.send(json.dumps({'error': 'Empty message'}))
            return

        msg_id = str(uuid.uuid4())

        user = self.scope['user']
        top_genres, recent_movies = await self._get_user_context(user)

        system_prompt = (
            'Ты помощник по выбору фильмов CineFind.\n'
            f'Любимые жанры пользователя: {", ".join(top_genres) if top_genres else "не определены"}.\n'
            f'Последние просмотренные: {", ".join(recent_movies) if recent_movies else "нет данных"}.\n'
            'Предлагай конкретные фильмы с кратким описанием почему они подойдут. '
            'Отвечай на русском языке.'
        )

        await self._stream_gigachat(msg_id, system_prompt, user_message)

    def _get_access_token(self, credentials: str) -> str:
        resp = requests.post(
            GIGACHAT_OAUTH_URL,
            headers={
                'Authorization': f'Basic {credentials}',
                'RqUID': str(uuid.uuid4()),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={'scope': 'GIGACHAT_API_PERS'},
            verify=False,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()['access_token']

    async def _stream_gigachat(self, msg_id, system_prompt, user_message):
        credentials = settings.GIGACHAT_API_KEY
        if not credentials:
            await self.send(json.dumps({'error': 'GigaChat API key not configured'}))
            return

        await self.send(json.dumps({'type': 'start', 'id': msg_id}))

        try:
            access_token = self._get_access_token(credentials)
        except requests.RequestException as exc:
            logger.error('GigaChat OAuth failed: %s', exc, exc_info=True)
            await self.send(json.dumps({'type': 'end', 'id': msg_id}))
            await self.send(json.dumps({'error': f'GigaChat auth failed: {exc}'}))
            return

        payload = {
            'model': 'GigaChat',
            'stream': True,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
        }
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                GIGACHAT_API_URL,
                json=payload,
                headers=headers,
                stream=True,
                timeout=30,
                verify=False,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8')
                if not decoded.startswith('data: '):
                    continue
                chunk_str = decoded[len('data: '):]
                if chunk_str == '[DONE]':
                    await self.send(json.dumps({'type': 'end', 'id': msg_id}))
                    break
                try:
                    chunk = json.loads(chunk_str)
                    delta = chunk['choices'][0]['delta'].get('content', '').replace('**', '')
                    if delta:
                        await self.send(json.dumps({'type': 'chunk', 'id': msg_id, 'content': delta}))
                except (KeyError, json.JSONDecodeError):
                    continue

        except requests.RequestException as exc:
            logger.error('GigaChat request failed: %s', exc, exc_info=True)
            await self.send(json.dumps({'type': 'end', 'id': msg_id}))
            await self.send(json.dumps({'error': f'Failed to reach GigaChat API: {exc}'}))

    @database_sync_to_async
    def _get_user_context(self, user):
        if not user or not user.is_authenticated:
            return [], []

        from collections import defaultdict
        from apps.events.models import UserEvent

        events = (
            UserEvent.objects
            .filter(user=user)
            .select_related('movie')
            .prefetch_related('movie__genres')
            .order_by('-timestamp')
        )

        genre_scores = defaultdict(float)
        recent_movies = []

        for event in events:
            if event.movie_id and event.event_type == 'movie_open':
                if len(recent_movies) < 5:
                    recent_movies.append(event.movie.title)

            if not event.movie_id:
                continue

            genres = list(event.movie.genres.all())
            if event.event_type == 'movie_open':
                for g in genres:
                    genre_scores[g.name] += 1
            elif event.event_type == 'time_on_page' and event.value and event.value > 60:
                for g in genres:
                    genre_scores[g.name] += 2
            elif event.event_type == 'trailer_play':
                for g in genres:
                    genre_scores[g.name] += 3
            elif event.event_type == 'watchlist_add':
                for g in genres:
                    genre_scores[g.name] += 5
            elif event.event_type == 'rating_set' and event.value is not None:
                delta = 8 if event.value >= 8 else (-5 if event.value <= 4 else 0)
                for g in genres:
                    genre_scores[g.name] += delta

        top_genres = sorted(genre_scores, key=genre_scores.__getitem__, reverse=True)[:3]
        return top_genres, recent_movies
