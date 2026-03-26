import asyncio
import logging
from collections import Counter

import httpx

from app.application.interfaces.music_gateway import MusicGateway

logger = logging.getLogger(__name__)

DEEZER_SEARCH_URL = "https://api.deezer.com/search"


class HttpMusicGateway(MusicGateway):
    async def search_track(self, query: str, limit: int = 1) -> list[dict]:
        """Поиск трека в Deezer по произвольному запросу."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                DEEZER_SEARCH_URL,
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            return [self._map_deezer_track(t) for t in data]

    async def get_track_info(self, track_id: str) -> dict | None:
        """Получение информации о треке по ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.deezer.com/track/{track_id}")
            if response.status_code != 200:
                return None
            return self._map_deezer_track(response.json())

    async def search_by_artist_and_title(self, artist: str, title: str) -> dict | None:
        """
        Поиск трека в Deezer по исполнителю и названию.
        Если не найден — пробует поиск только по названию.
        Проверяет совпадение артиста.
        """
        # Попытка 1: artist + track
        query = f'artist:"{artist}" track:"{title}"'
        try:
            results = await self.search_track(query)
            if results and self._artist_matches(artist, results[0].get("artist", "")):
                return results[0]
        except Exception as e:
            logger.warning("Deezer search failed for '%s': %s", query, e)

        # Попытка 2: только название трека
        try:
            results = await self.search_track(title)
            if results and self._artist_matches(artist, results[0].get("artist", "")):
                return results[0]
        except Exception as e:
            logger.warning("Deezer fallback search failed for '%s': %s", title, e)

        return None

    async def search_artist_tracks(self, artist: str, limit: int = 10) -> list[dict]:
        """Прямой поиск треков артиста в Deezer."""
        query = f'artist:"{artist}"'
        try:
            return await self.search_track(query, limit=limit)
        except Exception as e:
            logger.warning("Deezer artist search failed for '%s': %s", artist, e)
            return []

    async def enrich_tracks(self, suggestions: list[dict]) -> list[dict]:
        """
        Обогащение списка треков от GigaChat данными из Deezer.
        Если большинство треков от одного артиста — используется прямой поиск по артисту.
        """
        dominant_artist = self._detect_dominant_artist(suggestions)

        if dominant_artist:
            return await self._enrich_by_artist(dominant_artist, suggestions)

        return await self._enrich_by_titles(suggestions)

    async def _enrich_by_artist(self, artist: str, suggestions: list[dict]) -> list[dict]:
        """Стратегия обогащения для запросов по конкретному артисту."""
        desired_count = len(suggestions)

        # Параллельно: обогащение по названиям + прямой поиск по артисту
        title_enriched = await self._enrich_by_titles(suggestions)

        await asyncio.sleep(0.2)
        artist_tracks = await self.search_artist_tracks(artist, limit=desired_count)

        # Выбираем лучший результат
        if len(artist_tracks) > len(title_enriched):
            # Убираем дубликаты по title (case-insensitive)
            seen = set()
            unique = []
            for t in artist_tracks:
                key = t["title"].lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(t)
            return unique[:desired_count]

        return title_enriched

    async def _enrich_by_titles(self, suggestions: list[dict]) -> list[dict]:
        """Стандартное обогащение: поиск каждого трека по названию + артисту."""
        enriched = []
        deezer_available = True

        for suggestion in suggestions:
            if not deezer_available:
                enriched.append(suggestion)
                continue

            try:
                found = await self.search_by_artist_and_title(
                    suggestion.get("artist", ""),
                    suggestion.get("title", ""),
                )
            except Exception as e:
                logger.error("Deezer API недоступен: %s", e)
                deezer_available = False
                enriched.append(suggestion)
                continue

            if found:
                enriched.append(found)

            # Rate limiting
            await asyncio.sleep(0.2)

        return enriched

    @staticmethod
    def _detect_dominant_artist(suggestions: list[dict]) -> str | None:
        """
        Определяет, запрашивал ли пользователь конкретного артиста.
        Если большинство (>= 60%) треков от одного артиста — возвращает его имя.
        """
        if not suggestions:
            return None

        artists = [s.get("artist", "").strip().lower() for s in suggestions if s.get("artist")]
        if not artists:
            return None

        counter = Counter(artists)
        most_common_artist, count = counter.most_common(1)[0]

        if count >= len(suggestions) * 0.6:
            # Возвращаем оригинальное написание (не lower) первого совпадения
            for s in suggestions:
                if s.get("artist", "").strip().lower() == most_common_artist:
                    return s["artist"].strip()

        return None

    @staticmethod
    def _artist_matches(expected: str, actual: str) -> bool:
        """Проверяет, совпадает ли артист (нечёткое сравнение)."""
        if not expected or not actual:
            return True  # Нет данных для сравнения — не фильтруем

        expected_lower = expected.strip().lower()
        actual_lower = actual.strip().lower()

        # Точное совпадение
        if expected_lower == actual_lower:
            return True

        # Один содержится в другом (для случаев "Queen" vs "Queen & Adam Lambert")
        if expected_lower in actual_lower or actual_lower in expected_lower:
            return True

        return False

    @staticmethod
    def _map_deezer_track(track: dict) -> dict:
        """Маппинг ответа Deezer в единый формат."""
        return {
            "title": track.get("title", ""),
            "artist": track.get("artist", {}).get("name", ""),
            "cover_url": track.get("album", {}).get("cover_medium", ""),
            "duration": track.get("duration", 0),
            "url": track.get("link", ""),
        }
