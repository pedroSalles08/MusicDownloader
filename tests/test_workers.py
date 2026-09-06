from __future__ import annotations

from pathlib import Path

from music_downloader.download_profiles import DownloadProfile, VideoFormat
from music_downloader.models import (
    DownloadBatchResult,
    DownloadProgress,
    DownloadProgressStatus,
    DownloadResult,
    DownloadStatus,
    SearchBatchResult,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from music_downloader.workers import DownloadWorker, SearchWorker


def found(query: str = "query") -> SearchResult:
    return SearchResult(
        query=query,
        status=SearchStatus.FOUND,
        title="Title",
        id="id",
        url="https://video.example/id",
    )


class EmittingSearchService:
    def search_batch(self, queries, *, cancellation, progress_callback):
        results = []
        for index, query in enumerate(queries, start=1):
            if cancellation.cancelled:
                break
            result = found(query)
            results.append(result)
            progress_callback(SearchProgress(index, len(queries), result))
        return SearchBatchResult(tuple(results), cancellation.cancelled)


class EmittingDownloadService:
    def __init__(self) -> None:
        self.received_profile = None

    def download_batch(
        self,
        approved_results,
        output_directory,
        *,
        profile,
        embed_thumbnail,
        aria2c_path,
        cookie_browser,
        cancellation,
        progress_callback,
    ):
        self.received_profile = profile
        items = tuple(approved_results)
        results = []
        for index, item in enumerate(items, start=1):
            if cancellation.cancelled:
                break
            progress_callback(
                DownloadProgress(
                    query=item.query,
                    id=item.id,
                    item_index=index,
                    total_items=len(items),
                    processed_items=index - 1,
                    status=DownloadProgressStatus.DOWNLOADING,
                    item_fraction=0.5,
                )
            )
            results.append(
                DownloadResult(
                    query=item.query,
                    id=item.id,
                    status=DownloadStatus.COMPLETED,
                    output_path=Path(output_directory) / f"{item.id}.mp3",
                    attempts=1,
                )
            )
        return DownloadBatchResult(tuple(results), cancellation.cancelled)


def test_search_worker_emits_progress_and_completion(qtbot) -> None:
    worker = SearchWorker(EmittingSearchService(), ["one", "two"])

    with qtbot.waitSignal(worker.completed, timeout=1000) as completed:
        with qtbot.waitSignals([worker.progress, worker.progress], timeout=1000):
            worker.run()

    assert completed.args[0] == 0
    batch = completed.args[1]
    assert [result.query for result in batch.results] == ["one", "two"]
    assert not batch.cancelled


def test_search_worker_cancel_signal_is_cooperative(qtbot) -> None:
    worker = SearchWorker(EmittingSearchService(), ["one"])
    worker.cancel()

    with qtbot.waitSignal(worker.completed, timeout=1000) as completed:
        worker.run()

    assert completed.args[1].cancelled
    assert completed.args[1].results == ()


def test_download_worker_emits_progress_and_completion(qtbot, tmp_path: Path) -> None:
    service = EmittingDownloadService()
    profile = DownloadProfile.for_video(VideoFormat.WEBM, max_height=720)
    worker = DownloadWorker(
        service,
        [found()],
        tmp_path,
        profile=profile,
        embed_thumbnail=True,
        aria2c_path="aria2c",
        cookie_browser="firefox",
    )

    with qtbot.waitSignal(worker.completed, timeout=1000) as completed:
        with qtbot.waitSignal(worker.progress, timeout=1000):
            worker.run()

    assert completed.args[1].successful_count == 1
    assert service.received_profile == profile


def test_download_worker_cancel_is_cooperative(qtbot, tmp_path: Path) -> None:
    worker = DownloadWorker(
        EmittingDownloadService(),
        [found()],
        tmp_path,
        embed_thumbnail=False,
        aria2c_path=None,
    )
    worker.cancel()

    with qtbot.waitSignal(worker.completed, timeout=1000) as completed:
        worker.run()

    assert completed.args[1].cancelled
    assert completed.args[1].results == ()


def test_worker_preserves_unexpected_error_diagnostic(qtbot) -> None:
    class BrokenService:
        def search_batch(self, *_args, **_kwargs):
            raise RuntimeError("worker exploded")

    worker = SearchWorker(BrokenService(), ["query"])

    with qtbot.waitSignal(worker.failed, timeout=1000) as failed:
        worker.run()

    assert failed.args == [0, "RuntimeError: worker exploded"]
