from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Any

import pytest

from music_downloader.cancellation import CancellationToken
from music_downloader.models import SearchProgress, SearchStatus
from music_downloader.search_service import SearchService


class FakeYoutubeDL:
    def __init__(
        self,
        options: dict[str, Any],
        behavior: dict[str, Any] | None | Exception,
        calls: list[tuple[str, bool]],
    ) -> None:
        self.options = options
        self.behavior = behavior
        self.calls = calls

    def __enter__(self) -> FakeYoutubeDL:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def extract_info(self, url: str, *, download: bool) -> dict[str, Any] | None:
        self.calls.append((url, download))
        if isinstance(self.behavior, Exception):
            raise self.behavior
        return self.behavior


class FakeFactory:
    def __init__(self, behaviors: list[dict[str, Any] | None | Exception]) -> None:
        self.behaviors = list(behaviors)
        self.options: list[dict[str, Any]] = []
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, options: dict[str, Any]) -> FakeYoutubeDL:
        self.options.append(options)
        return FakeYoutubeDL(options, self.behaviors.pop(0), self.calls)


def found_info(identifier: str = "video-id") -> dict[str, Any]:
    return {
        "entries": [
            {
                "id": identifier,
                "title": "Found title",
                "channel": "Found channel",
                "duration": 123,
                "webpage_url": f"https://video.example/{identifier}",
                "thumbnail": "https://image.example/cover.jpg",
            }
        ]
    }


def test_search_uses_single_result_without_downloading_and_maps_metadata() -> None:
    factory = FakeFactory([found_info()])

    batch = SearchService(factory).search_batch(["query text"])

    assert factory.calls == [("ytsearch1:query text", False)]
    options = factory.options[0]
    assert options["skip_download"] is True
    assert options["noplaylist"] is True
    assert options["js_runtimes"] == {"node": {}}
    result = batch.results[0]
    assert result.status is SearchStatus.FOUND
    assert result.query == "query text"
    assert result.title == "Found title"
    assert result.channel == "Found channel"
    assert result.duration == 123.0
    assert result.id == "video-id"
    assert result.url == "https://video.example/video-id"
    assert result.thumbnail == "https://image.example/cover.jpg"


@pytest.mark.parametrize("info", [None, {"entries": []}, {"entries": [None]}])
def test_no_result_is_an_explicit_status(info: dict[str, Any] | None) -> None:
    batch = SearchService(FakeFactory([info])).search_batch(["missing"])

    assert batch.results[0].status is SearchStatus.NO_RESULT
    assert batch.results[0].error is None


def test_search_skips_noise_and_uses_later_candidate_with_url() -> None:
    info = {
        "entries": [
            None,
            "noise",
            {},
            {"title": "No locator"},
            {
                "title": "Useful result",
                "url": "https://media.example/useful",
            },
        ]
    }

    result = SearchService(FakeFactory([info])).search_batch(["query"]).results[0]

    assert result.status is SearchStatus.FOUND
    assert result.title == "Useful result"
    assert result.url == "https://media.example/useful"


def test_search_builds_stable_url_fallback_from_id() -> None:
    info = {"entries": [{"id": "fallback-id", "title": "ID only"}]}

    result = SearchService(FakeFactory([info])).search_batch(["query"]).results[0]

    assert result.status is SearchStatus.FOUND
    assert result.id == "fallback-id"
    assert result.url == "https://www.youtube.com/watch?v=fallback-id"


def test_search_does_not_mark_mapping_without_id_or_url_as_found() -> None:
    info = {"entries": [{"title": "Metadata without locator"}, {}, None]}

    result = SearchService(FakeFactory([info])).search_batch(["query"]).results[0]

    assert result.status is SearchStatus.NO_RESULT
    assert result.url is None


def test_failure_is_diagnostic_and_does_not_abort_batch() -> None:
    factory = FakeFactory([OSError("network offline"), found_info("second")])
    progress: list[SearchProgress] = []

    batch = SearchService(factory).search_batch(
        ["first", "second"], progress_callback=progress.append
    )

    assert [result.status for result in batch.results] == [
        SearchStatus.ERROR,
        SearchStatus.FOUND,
    ]
    assert batch.results[0].error == "OSError: network offline"
    assert [event.processed_items for event in progress] == [1, 2]
    assert all(event.total_items == 2 for event in progress)


def test_cancellation_before_search_avoids_factory() -> None:
    token = CancellationToken()
    token.cancel()
    factory = FakeFactory([found_info()])

    batch = SearchService(factory).search_batch(["first"], cancellation=token)

    assert batch.cancelled
    assert batch.results == ()
    assert factory.options == []


def test_cancellation_between_searches_returns_completed_prefix() -> None:
    token = CancellationToken()
    factory = FakeFactory([found_info("first"), found_info("second")])

    def cancel_after_first(_progress: SearchProgress) -> None:
        token.cancel()

    batch = SearchService(factory).search_batch(
        ["first", "second"],
        cancellation=token,
        progress_callback=cancel_after_first,
    )

    assert batch.cancelled
    assert len(batch.results) == 1
    assert factory.calls == [("ytsearch1:first", False)]
