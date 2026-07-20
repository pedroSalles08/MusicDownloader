"""Recognition helpers for Spotify input handled outside the MVP."""

from __future__ import annotations

from urllib.parse import urlsplit


def is_spotify_playlist_url(value: str) -> bool:
    """Return whether *value* is a public open.spotify.com playlist URL."""

    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme.casefold() not in {"http", "https"}:
        return False
    if hostname is None or hostname.casefold() != "open.spotify.com":
        return False
    default_port = 443 if parsed.scheme.casefold() == "https" else 80
    if port is not None and port != default_port:
        return False

    segments = [segment for segment in parsed.path.split("/") if segment]
    return len(segments) == 2 and segments[0] == "playlist" and bool(segments[1])
