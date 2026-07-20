import pytest

from music_downloader.spotify import is_spotify_playlist_url


@pytest.mark.parametrize(
    "url",
    [
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "http://OPEN.SPOTIFY.COM/playlist/abc123/",
        "  https://open.spotify.com/playlist/abc123?si=token  ",
    ],
)
def test_detects_spotify_playlist_urls(url: str) -> None:
    assert is_spotify_playlist_url(url)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "open.spotify.com/playlist/abc123",
        "https://open.spotify.com/track/abc123",
        "https://open.spotify.com/playlist/",
        "https://open.spotify.com/playlist/abc123/extra",
        "https://open.spotify.com.evil.example/playlist/abc123",
        "spotify:playlist:abc123",
    ],
)
def test_rejects_other_values(value: str) -> None:
    assert not is_spotify_playlist_url(value)


def test_rejects_malformed_url_without_raising() -> None:
    assert not is_spotify_playlist_url("https://open.spotify.com:invalid/playlist/id")
