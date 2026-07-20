"""Detection of native media tools required by download services."""

from __future__ import annotations

from collections.abc import Callable
import shutil

from music_downloader.models import ExecutableStatus, MediaToolsStatus

ExecutableResolver = Callable[[str], str | None]


def detect_media_tools(
    resolver: ExecutableResolver = shutil.which,
) -> MediaToolsStatus:
    """Detect FFmpeg and FFprobe using an injectable executable resolver."""

    return MediaToolsStatus(
        ffmpeg=ExecutableStatus(name="ffmpeg", path=resolver("ffmpeg")),
        ffprobe=ExecutableStatus(name="ffprobe", path=resolver("ffprobe")),
    )
