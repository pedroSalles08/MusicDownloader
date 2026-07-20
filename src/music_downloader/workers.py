"""Qt workers that coordinate services without importing widgets."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from music_downloader.cancellation import CancellationToken
from music_downloader.diagnostics import exception_diagnostic
from music_downloader.models import SearchResult


class SearchWorker(QObject):
    progress = Signal(int, object)
    completed = Signal(int, object)
    failed = Signal(int, str)

    def __init__(
        self, service: Any, queries: Iterable[str], *, generation: int = 0
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = tuple(queries)
        self._generation = generation
        self._cancellation = CancellationToken()

    @property
    def cancellation(self) -> CancellationToken:
        return self._cancellation

    def cancel(self) -> None:
        self._cancellation.cancel()

    @Slot()
    def run(self) -> None:
        try:
            result = self._service.search_batch(
                self._queries,
                cancellation=self._cancellation,
                progress_callback=lambda progress: self.progress.emit(
                    self._generation, progress
                ),
            )
        except Exception as error:
            self.failed.emit(self._generation, exception_diagnostic(error))
            return
        self.completed.emit(self._generation, result)


class DownloadWorker(QObject):
    progress = Signal(int, object)
    completed = Signal(int, object)
    failed = Signal(int, str)

    def __init__(
        self,
        service: Any,
        approved_results: Iterable[SearchResult],
        output_directory: str | Path,
        *,
        embed_thumbnail: bool,
        aria2c_path: str | None,
        generation: int = 0,
    ) -> None:
        super().__init__()
        self._service = service
        self._approved_results = tuple(approved_results)
        self._output_directory = output_directory
        self._embed_thumbnail = embed_thumbnail
        self._aria2c_path = aria2c_path
        self._generation = generation
        self._cancellation = CancellationToken()

    @property
    def cancellation(self) -> CancellationToken:
        return self._cancellation

    def cancel(self) -> None:
        self._cancellation.cancel()

    @Slot()
    def run(self) -> None:
        try:
            result = self._service.download_batch(
                self._approved_results,
                self._output_directory,
                embed_thumbnail=self._embed_thumbnail,
                aria2c_path=self._aria2c_path,
                cancellation=self._cancellation,
                progress_callback=lambda progress: self.progress.emit(
                    self._generation, progress
                ),
            )
        except Exception as error:
            self.failed.emit(self._generation, exception_diagnostic(error))
            return
        self.completed.emit(self._generation, result)
