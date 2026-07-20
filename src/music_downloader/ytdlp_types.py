"""Minimal protocols that keep yt-dlp replaceable in deterministic tests."""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Any, Protocol, Self

import yt_dlp


class YoutubeDLClient(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def extract_info(self, url: str, *, download: bool) -> dict[str, Any] | None: ...


YoutubeDLFactory = Callable[[dict[str, Any]], YoutubeDLClient]


def default_ytdl_factory(options: dict[str, Any]) -> YoutubeDLClient:
    return yt_dlp.YoutubeDL(options)
