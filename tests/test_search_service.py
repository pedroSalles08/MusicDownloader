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


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=video-id",
        "https://music.youtube.com/watch?v=video-id",
        "https://youtu.be/video-id",
    ],
)
def test_youtube_video_url_is_resolved_directly_without_text_search(url: str) -> None:
    factory = FakeFactory(
        [
            {
                "id": "video-id",
                "title": "Exact linked video",
                "webpage_url": "https://www.youtube.com/watch?v=video-id",
            }
        ]
    )

    result = SearchService(factory).search_batch([url]).results[0]

    assert factory.calls == [(url, False)]
    assert factory.options[0]["noplaylist"] is True
    assert result.status is SearchStatus.FOUND
    assert result.query == url
    assert result.title == "Exact linked video"
    assert result.url == "https://www.youtube.com/watch?v=video-id"


def test_youtube_playlist_url_expands_every_available_video_in_order() -> None:
    playlist_url = "https://www.youtube.com/playlist?list=PL123"
    factory = FakeFactory(
        [
            {
                "entries": [
                    {
                        "id": "first-id",
                        "title": "First track",
                        "channel": "Channel one",
                        "url": "first-id",
                    },
                    None,
                    {
                        "id": "second-id",
                        "title": "Second track",
                        "webpage_url": "https://www.youtube.com/watch?v=second-id",
                    },
                ]
            }
        ]
    )
    progress: list[SearchProgress] = []

    batch = SearchService(factory).search_batch(
        [playlist_url], progress_callback=progress.append
    )

    assert factory.calls == [(playlist_url, False)]
    assert "noplaylist" not in factory.options[0]
    assert factory.options[0]["extract_flat"] == "in_playlist"
    assert factory.options[0]["lazy_playlist"] is True
    assert [result.title for result in batch.results] == [
        "First track",
        "Second track",
    ]
    assert [result.url for result in batch.results] == [
        "https://www.youtube.com/watch?v=first-id",
        "https://www.youtube.com/watch?v=second-id",
    ]
    assert [result.query for result in batch.results] == [
        "https://www.youtube.com/watch?v=first-id",
        "https://www.youtube.com/watch?v=second-id",
    ]
    assert [event.processed_items for event in progress] == [1, 1]
    assert all(event.total_items == 1 for event in progress)


def test_mixed_names_video_and_playlist_preserve_input_and_playlist_order() -> None:
    video_url = "https://youtu.be/direct-id"
    playlist_url = "https://www.youtube.com/watch?v=first&list=PL123"
    factory = FakeFactory(
        [
            found_info("search-id"),
            {
                "id": "direct-id",
                "title": "Direct",
                "webpage_url": "https://www.youtube.com/watch?v=direct-id",
            },
            {
                "entries": [
                    {
                        "id": "playlist-one",
                        "title": "Playlist one",
                    },
                    {
                        "id": "playlist-two",
                        "title": "Playlist two",
                    },
                ]
            },
        ]
    )

    batch = SearchService(factory).search_batch(
        ["Song Artist", video_url, playlist_url]
    )

    assert factory.calls == [
        ("ytsearch1:Song Artist", False),
        (video_url, False),
        (playlist_url, False),
    ]
    assert [result.id for result in batch.results] == [
        "search-id",
        "direct-id",
        "playlist-one",
        "playlist-two",
    ]
    assert [result.query for result in batch.results] == [
        "Song Artist",
        video_url,
        "https://www.youtube.com/watch?v=playlist-one",
        "https://www.youtube.com/watch?v=playlist-two",
    ]


def test_non_youtube_url_remains_a_text_search_query() -> None:
    value = "https://example.com/watch?v=not-youtube"
    factory = FakeFactory([found_info()])

    SearchService(factory).search_batch([value])

    assert factory.calls == [(f"ytsearch1:{value}", False)]


def test_empty_youtube_playlist_becomes_one_explicit_no_result() -> None:
    playlist_url = "https://www.youtube.com/playlist?list=EMPTY"
    factory = FakeFactory([{"entries": [None, {"title": "Unavailable"}]}])

    batch = SearchService(factory).search_batch([playlist_url])

    assert len(batch.results) == 1
    assert batch.results[0].query == playlist_url
    assert batch.results[0].status is SearchStatus.NO_RESULT


def test_cancellation_during_playlist_expansion_stops_before_next_entry() -> None:
    playlist_url = "https://www.youtube.com/playlist?list=PL123"
    factory = FakeFactory(
        [
            {
                "entries": [
                    {"id": "one", "title": "One"},
                    {"id": "two", "title": "Two"},
                    {"id": "three", "title": "Three"},
                ]
            }
        ]
    )
    token = CancellationToken()

    def cancel_after_first(_progress: SearchProgress) -> None:
        token.cancel()

    batch = SearchService(factory).search_batch(
        [playlist_url],
        cancellation=token,
        progress_callback=cancel_after_first,
    )

    assert batch.cancelled
    assert [result.id for result in batch.results] == ["one"]


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
