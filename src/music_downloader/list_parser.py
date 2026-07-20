"""Parser for the application's semicolon-separated text input."""

from __future__ import annotations

from music_downloader.models import QueryListResult
from music_downloader.text import normalized_dedupe_key


def parse_semicolon_list(value: str) -> QueryListResult:
    """Split, trim and stably deduplicate user queries.

    The first spelling of each query is preserved. Comparison uses Unicode NFKC
    normalization and ``casefold`` so casing and equivalent Unicode forms do
    not create duplicate queue items.
    """

    queries: list[str] = []
    seen: set[str] = set()
    duplicate_count = 0
    empty_count = 0

    for raw_query in value.split(";"):
        query = raw_query.strip()
        if not query:
            empty_count += 1
            continue

        key = normalized_dedupe_key(query)
        if key in seen:
            duplicate_count += 1
            continue

        seen.add(key)
        queries.append(query)

    return QueryListResult(
        queries=tuple(queries),
        duplicate_count=duplicate_count,
        empty_count=empty_count,
    )
