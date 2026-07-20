from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest
import yt_dlp

from music_downloader.cancellation import CancellationToken
from music_downloader.download_service import DownloadService, build_output_basename
from music_downloader.models import (
    DownloadProgress,
    DownloadProgressStatus,
    DownloadStatus,
    ExecutableStatus,
    MediaToolsStatus,
    SearchResult,
    SearchStatus,
)

Behavior = dict[str, Any] | Exception | Callable[[dict[str, Any]], dict[str, Any]]


class FakeYoutubeDL:
    def __init__(
        self,
        options: dict[str, Any],
        behavior: Behavior,
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

    def extract_info(self, url: str, *, download: bool) -> dict[str, Any]:
        self.calls.append((url, download))
        if isinstance(self.behavior, Exception):
            raise self.behavior
        if callable(self.behavior):
            return self.behavior(self.options)
        return self.behavior


class FakeFactory:
    def __init__(self, behaviors: list[Behavior]) -> None:
        self.behaviors = list(behaviors)
        self.options: list[dict[str, Any]] = []
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, options: dict[str, Any]) -> FakeYoutubeDL:
        self.options.append(options)
        return FakeYoutubeDL(options, self.behaviors.pop(0), self.calls)


def tools_available() -> MediaToolsStatus:
    return MediaToolsStatus(
        ffmpeg=ExecutableStatus("ffmpeg", r"C:\tools\ffmpeg.exe"),
        ffprobe=ExecutableStatus("ffprobe", r"C:\tools\ffprobe.exe"),
    )


def approved(
    query: str = "Song Artist",
    identifier: str = "video-id",
    title: str = "Song title",
) -> SearchResult:
    return SearchResult(
        query=query,
        status=SearchStatus.FOUND,
        title=title,
        id=identifier,
        url=f"https://video.example/watch/{identifier}",
    )


def service(factory: FakeFactory, **kwargs: Any) -> DownloadService:
    return DownloadService(factory, tool_detector=tools_available, **kwargs)


def test_download_uses_direct_url_and_expected_audio_options(tmp_path: Path) -> None:
    factory = FakeFactory([{}])

    batch = service(factory).download_batch([approved()], tmp_path / "new-folder")

    assert factory.calls == [("https://video.example/watch/video-id", True)]
    assert "ytsearch" not in factory.calls[0][0]
    options = factory.options[0]
    assert options["format"] == "bestaudio/best"
    assert options["continuedl"] is True
    assert options["retries"] == 10
    assert options["fragment_retries"] == 10
    assert options["concurrent_fragment_downloads"] == 8
    assert options["js_runtimes"] == {"node": {}}
    assert options["noplaylist"] is True
    assert (tmp_path / "new-folder").is_dir()
    assert batch.results[0].status is DownloadStatus.COMPLETED
    assert batch.results[0].output_path == tmp_path / "new-folder" / "Song title [video-id].mp3"


@pytest.mark.parametrize("embed_thumbnail", [False, True])
def test_thumbnail_options_are_optional(
    tmp_path: Path, embed_thumbnail: bool
) -> None:
    factory = FakeFactory([{}])

    service(factory).download_batch(
        [approved()], tmp_path, embed_thumbnail=embed_thumbnail
    )

    options = factory.options[0]
    keys = [postprocessor["key"] for postprocessor in options["postprocessors"]]
    assert options["writethumbnail"] is embed_thumbnail
    assert keys[:2] == ["FFmpegExtractAudio", "FFmpegMetadata"]
    assert ("EmbedThumbnail" in keys) is embed_thumbnail
    assert options["postprocessors"][0]["preferredquality"] == "192"


@pytest.mark.parametrize("aria2c_path", [None, r"C:\tools\aria2c.exe"])
def test_aria2c_options_are_optional(tmp_path: Path, aria2c_path: str | None) -> None:
    factory = FakeFactory([{}])

    service(factory).download_batch([approved()], tmp_path, aria2c_path=aria2c_path)

    options = factory.options[0]
    if aria2c_path:
        assert options["external_downloader"] == aria2c_path
        assert options["external_downloader_args"] == {"aria2c": ["-k", "1M"]}
    else:
        assert "external_downloader" not in options
        assert "external_downloader_args" not in options


def test_transient_errors_retry_three_times_with_injected_waiter(tmp_path: Path) -> None:
    factory = FakeFactory(
        [
            yt_dlp.utils.DownloadError("temporary one"),
            yt_dlp.utils.DownloadError("temporary two"),
            {},
        ]
    )
    waits: list[float] = []

    batch = service(
        factory, waiter=lambda delay, _token: waits.append(delay)
    ).download_batch([approved()], tmp_path)

    assert waits == [2.0, 5.0]
    assert len(factory.calls) == 3
    assert batch.results[0].status is DownloadStatus.COMPLETED
    assert batch.results[0].attempts == 3


def test_progress_hook_reports_item_and_total_progress(tmp_path: Path) -> None:
    def emit_hooks(options: dict[str, Any]) -> dict[str, Any]:
        hook = options["progress_hooks"][0]
        hook({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})
        hook({"status": "finished", "downloaded_bytes": 100, "total_bytes": 100})
        return {}

    events: list[DownloadProgress] = []

    service(FakeFactory([emit_hooks])).download_batch(
        [approved()], tmp_path, progress_callback=events.append
    )

    assert [event.status for event in events] == [
        DownloadProgressStatus.DOWNLOADING,
        DownloadProgressStatus.PROCESSING,
        DownloadProgressStatus.COMPLETED,
    ]
    assert events[0].item_fraction == 0.5
    assert events[0].downloaded_bytes == 50
    assert events[0].total_bytes == 100
    assert all(event.item_index == 1 and event.total_items == 1 for event in events)
    assert events[-1].processed_items == 1


def test_missing_ffprobe_stops_before_factory_with_guidance(tmp_path: Path) -> None:
    factory = FakeFactory([{}])
    missing = MediaToolsStatus(
        ffmpeg=ExecutableStatus("ffmpeg", r"C:\tools\ffmpeg.exe"),
        ffprobe=ExecutableStatus("ffprobe", None),
    )
    downloader = DownloadService(factory, tool_detector=lambda: missing)

    batch = downloader.download_batch([approved()], tmp_path / "not-created")

    assert batch.preflight_error is not None
    assert "ffprobe" in batch.preflight_error
    assert "Instale o FFmpeg" in batch.preflight_error
    assert factory.calls == []
    assert not (tmp_path / "not-created").exists()


def test_safe_names_include_ids_and_resist_collision(tmp_path: Path) -> None:
    first = approved("one", "id:one", 'CON<>:"/\\|?*')
    second = approved("two", "id?two", 'CON<>:"/\\|?*')
    factory = FakeFactory([{}, {}])

    batch = service(factory).download_batch([first, second], tmp_path)

    names = [result.output_path.name for result in batch.results if result.output_path]
    assert len(names) == 2
    assert len(set(names)) == 2
    assert all(not set('<>:"/\\|?*').intersection(name) for name in names)
    assert "[id_one-" in build_output_basename(first)


def test_identical_title_and_id_are_reserved_uniquely_with_matching_templates(
    tmp_path: Path,
) -> None:
    item = approved()
    factory = FakeFactory([{}, {}])

    batch = service(factory).download_batch([item, item], tmp_path)

    paths = [result.output_path for result in batch.results]
    assert paths == [
        tmp_path / "Song title [video-id].mp3",
        tmp_path / "Song title [video-id] (2).mp3",
    ]
    assert all(result.status is DownloadStatus.COMPLETED for result in batch.results)
    for result, options in zip(batch.results, factory.options, strict=True):
        assert result.output_path is not None
        assert Path(options["outtmpl"]) == result.output_path.with_suffix(".%(ext)s")


def test_raw_ids_that_sanitize_equally_keep_distinct_stable_hashes(
    tmp_path: Path,
) -> None:
    first = approved("one", "same:id")
    second = approved("two", "same?id")
    factory = FakeFactory([{}, {}])

    batch = service(factory).download_batch([first, second], tmp_path)

    paths = [result.output_path for result in batch.results]
    assert None not in paths
    assert paths[0] != paths[1]
    assert all("[same_id-" in path.name for path in paths if path)
    assert build_output_basename(first) == build_output_basename(first)
    assert build_output_basename(first) != build_output_basename(second)


def test_existing_output_and_intermediate_files_advance_ordinal(
    tmp_path: Path,
) -> None:
    (tmp_path / "Song title [video-id].mp3").write_bytes(b"existing")
    (tmp_path / "Song title [video-id] (2).webm.part").write_bytes(b"partial")
    factory = FakeFactory([{}])

    batch = service(factory).download_batch([approved()], tmp_path)

    expected = tmp_path / "Song title [video-id] (3).mp3"
    assert batch.results[0].output_path == expected
    assert Path(factory.options[0]["outtmpl"]) == expected.with_suffix(".%(ext)s")


def test_cancellation_before_batch_skips_preflight_and_factory(tmp_path: Path) -> None:
    token = CancellationToken()
    token.cancel()
    factory = FakeFactory([{}])
    detections: list[bool] = []
    downloader = DownloadService(
        factory,
        tool_detector=lambda: detections.append(True) or tools_available(),
    )

    batch = downloader.download_batch([approved()], tmp_path, cancellation=token)

    assert batch.cancelled
    assert batch.results == ()
    assert detections == []
    assert factory.calls == []


@pytest.mark.parametrize("cancelled", [False, True])
def test_empty_batch_has_no_preflight_or_filesystem_side_effect(
    tmp_path: Path, cancelled: bool
) -> None:
    token = CancellationToken()
    if cancelled:
        token.cancel()
    destination = tmp_path / "must-not-exist"
    factory = FakeFactory([])

    def unexpected_detection() -> MediaToolsStatus:
        pytest.fail("empty batch must not detect tools")

    downloader = DownloadService(factory, tool_detector=unexpected_detection)
    batch = downloader.download_batch([], destination, cancellation=token)

    assert batch.results == ()
    assert batch.cancelled is cancelled
    assert batch.preflight_error is None
    assert not destination.exists()
    assert factory.calls == []


def test_nul_destination_is_a_preflight_error_instead_of_escaping() -> None:
    factory = FakeFactory([{}])

    batch = service(factory).download_batch([approved()], "invalid\x00destination")

    assert batch.results == ()
    assert batch.preflight_error is not None
    assert batch.preflight_error.startswith("ValueError:")
    assert factory.calls == []


def test_cancellation_between_items_keeps_completed_prefix(tmp_path: Path) -> None:
    token = CancellationToken()
    factory = FakeFactory([{}, {}])

    def cancel_after_completion(progress: DownloadProgress) -> None:
        if progress.status is DownloadProgressStatus.COMPLETED:
            token.cancel()

    batch = service(factory).download_batch(
        [approved("first", "first"), approved("second", "second")],
        tmp_path,
        cancellation=token,
        progress_callback=cancel_after_completion,
    )

    assert batch.cancelled
    assert len(batch.results) == 1
    assert batch.results[0].status is DownloadStatus.COMPLETED
    assert factory.calls == [("https://video.example/watch/first", True)]


def test_cancellation_during_hook_stops_current_item(tmp_path: Path) -> None:
    token = CancellationToken()

    def emit_hook(options: dict[str, Any]) -> dict[str, Any]:
        options["progress_hooks"][0](
            {"status": "downloading", "downloaded_bytes": 1, "total_bytes": 10}
        )
        pytest.fail("hook cancellation should interrupt extract_info")

    def cancel_on_download(progress: DownloadProgress) -> None:
        if progress.status is DownloadProgressStatus.DOWNLOADING:
            token.cancel()

    batch = service(FakeFactory([emit_hook])).download_batch(
        [approved()],
        tmp_path,
        cancellation=token,
        progress_callback=cancel_on_download,
    )

    assert batch.cancelled
    assert batch.results[0].status is DownloadStatus.CANCELLED
    assert batch.results[0].attempts == 1


def test_cancellation_during_retry_wait_does_not_start_next_attempt(
    tmp_path: Path,
) -> None:
    token = CancellationToken()
    factory = FakeFactory([yt_dlp.utils.DownloadError("temporary"), {}])

    def cancel_wait(_delay: float, received_token: CancellationToken) -> None:
        received_token.cancel()

    batch = service(factory, waiter=cancel_wait).download_batch(
        [approved()], tmp_path, cancellation=token
    )

    assert batch.cancelled
    assert len(factory.calls) == 1
    assert batch.results[0].status is DownloadStatus.CANCELLED


def test_unexpected_item_failure_does_not_abort_and_keeps_diagnostic(
    tmp_path: Path,
) -> None:
    factory = FakeFactory([RuntimeError("unexpected decoder failure"), {}])

    batch = service(factory).download_batch(
        [approved("first", "first"), approved("second", "second")], tmp_path
    )

    assert [result.status for result in batch.results] == [
        DownloadStatus.ERROR,
        DownloadStatus.COMPLETED,
    ]
    assert batch.results[0].error == "RuntimeError: unexpected decoder failure"
    assert batch.successful_count == 1
    assert batch.failed_count == 1
