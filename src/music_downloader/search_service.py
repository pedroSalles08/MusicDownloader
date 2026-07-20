"""Network-search service isolated from UI and download concerns."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from music_downloader.cancellation import CancellationToken
from music_downloader.diagnostics import exception_diagnostic
from music_downloader.models import (
    SearchBatchResult,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from music_downloader.ytdlp_types import YoutubeDLFactory, default_ytdl_factory

SearchProgressCallback = Callable[[SearchProgress], None]


def search_options() -> dict[str, Any]:
    """Return yt-dlp options for metadata-only single-result searches."""

    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 30,
        "retries": 3,
        "js_runtimes": {"node": {}},
    }


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _entry_url(entry: Mapping[str, Any]) -> str | None:
    url = _optional_text(entry.get("webpage_url")) or _optional_text(entry.get("url"))
    if url:
        return url

    media_id = _optional_text(entry.get("id"))
    if media_id:
        return f"https://www.youtube.com/watch?v={media_id}"
    return None


def _first_entry(info: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not info:
        return None

    entries = info.get("entries")
    if entries is None:
        return info if _entry_url(info) else None

    for entry in entries:
        if isinstance(entry, Mapping) and _entry_url(entry):
            return entry
    return None


def _duration(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _thumbnail(entry: Mapping[str, Any]) -> str | None:
    direct = _optional_text(entry.get("thumbnail"))
    if direct:
        return direct

    thumbnails = entry.get("thumbnails")
    if isinstance(thumbnails, list):
        for candidate in reversed(thumbnails):
            if isinstance(candidate, Mapping):
                url = _optional_text(candidate.get("url"))
                if url:
                    return url
    return None


def _found_result(query: str, entry: Mapping[str, Any]) -> SearchResult:
    media_id = _optional_text(entry.get("id"))
    url = _entry_url(entry)

    return SearchResult(
        query=query,
        status=SearchStatus.FOUND,
        title=_optional_text(entry.get("title")),
        channel=_optional_text(entry.get("channel"))
        or _optional_text(entry.get("uploader")),
        duration=_duration(entry.get("duration")),
        id=media_id,
        url=url,
        thumbnail=_thumbnail(entry),
    )


class SearchService:
    def __init__(self, ytdl_factory: YoutubeDLFactory = default_ytdl_factory) -> None:
        self._ytdl_factory = ytdl_factory

    def search_batch(
        self,
        queries: Iterable[str],
        *,
        cancellation: CancellationToken | None = None,
        progress_callback: SearchProgressCallback | None = None,
    ) -> SearchBatchResult:
        """Search sequentially, isolating every query failure from the batch."""

        token = cancellation or CancellationToken()
        pending = tuple(queries)
        results: list[SearchResult] = []

        for query in pending:
            if token.cancelled:
                break

            result = self._search_one(query)
            results.append(result)
            if progress_callback:
                progress_callback(
                    SearchProgress(
                        processed_items=len(results),
                        total_items=len(pending),
                        result=result,
                    )
                )

        return SearchBatchResult(results=tuple(results), cancelled=token.cancelled)

    def _search_one(self, query: str) -> SearchResult:
        try:
            with self._ytdl_factory(search_options()) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entry = _first_entry(info)
            if entry is None:
                return SearchResult(query=query, status=SearchStatus.NO_RESULT)
            return _found_result(query, entry)
        except Exception as error:
            return SearchResult(
                query=query,
                status=SearchStatus.ERROR,
                error=exception_diagnostic(error),
            )
