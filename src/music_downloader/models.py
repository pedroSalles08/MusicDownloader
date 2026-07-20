"""Typed values shared by the input and system services."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass(frozen=True, slots=True)
class QueryListResult:
    """Normalized queries parsed from free-form semicolon input."""

    queries: tuple[str, ...]
    duplicate_count: int
    empty_count: int


@dataclass(frozen=True, slots=True)
class ImportedTrack:
    """One valid track read from a CSV source row."""

    title: str
    artist: str
    source_line: int

    @property
    def query(self) -> str:
        """Return the search query compatible with the original script."""

        return f"{self.title} {self.artist}"


@dataclass(frozen=True, slots=True)
class InvalidCsvRow:
    """A CSV row that could not become a search query."""

    source_line: int
    reason: str


@dataclass(frozen=True, slots=True)
class CsvImportResult:
    """Tracks and diagnostics produced by a complete CSV import."""

    tracks: tuple[ImportedTrack, ...]
    invalid_rows: tuple[InvalidCsvRow, ...]
    duplicate_count: int
    total_rows: int
    encoding: str

    @property
    def queries(self) -> tuple[str, ...]:
        return tuple(track.query for track in self.tracks)

    @property
    def imported_count(self) -> int:
        return len(self.tracks)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid_rows)


@dataclass(frozen=True, slots=True)
class ExecutableStatus:
    """Detection status for one required executable."""

    name: str
    path: str | None

    @property
    def available(self) -> bool:
        return self.path is not None


@dataclass(frozen=True, slots=True)
class MediaToolsStatus:
    """Detection result for the FFmpeg tool pair."""

    ffmpeg: ExecutableStatus
    ffprobe: ExecutableStatus

    @property
    def available(self) -> bool:
        return self.ffmpeg.available and self.ffprobe.available

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(
            tool.name for tool in (self.ffmpeg, self.ffprobe) if not tool.available
        )

    @property
    def guidance(self) -> str:
        if self.available:
            return "FFmpeg e FFprobe encontrados."

        missing = " e ".join(self.missing)
        return (
            f"Não foi possível encontrar {missing} no PATH. "
            "Instale o FFmpeg (que inclui o FFprobe) e reinicie o aplicativo."
        )


class SearchStatus(str, Enum):
    FOUND = "found"
    NO_RESULT = "no_result"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SearchResult:
    """One search outcome, including failures and empty searches."""

    query: str
    status: SearchStatus
    title: str | None = None
    channel: str | None = None
    duration: float | None = None
    id: str | None = None
    url: str | None = None
    thumbnail: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SearchProgress:
    """Batch-level progress emitted after each completed search."""

    processed_items: int
    total_items: int
    result: SearchResult


@dataclass(frozen=True, slots=True)
class SearchBatchResult:
    results: tuple[SearchResult, ...]
    cancelled: bool


class DownloadStatus(str, Enum):
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class DownloadProgressStatus(str, Enum):
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    RETRYING = "retrying"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class DownloadProgress:
    """Progress for the current item and its position in the whole batch."""

    query: str
    id: str | None
    item_index: int
    total_items: int
    processed_items: int
    status: DownloadProgressStatus
    item_fraction: float | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class DownloadResult:
    query: str
    id: str | None
    status: DownloadStatus
    output_path: Path | None
    attempts: int
    error: str | None = None


@dataclass(frozen=True, slots=True)
class DownloadBatchResult:
    results: tuple[DownloadResult, ...]
    cancelled: bool
    preflight_error: str | None = None

    @property
    def successful_count(self) -> int:
        return sum(result.status is DownloadStatus.COMPLETED for result in self.results)

    @property
    def failed_count(self) -> int:
        return sum(result.status is DownloadStatus.ERROR for result in self.results)
