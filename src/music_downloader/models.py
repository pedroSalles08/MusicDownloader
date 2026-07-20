"""Typed values shared by the input and system services."""

from __future__ import annotations

from dataclasses import dataclass


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
