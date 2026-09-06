from __future__ import annotations

import pytest

from music_downloader.browser_cookies import browser_from_prog_id


@pytest.mark.parametrize(
    ("prog_id", "expected"),
    [
        ("FirefoxURL-308046B0AF4A39CB", "firefox"),
        ("ChromeHTML", "chrome"),
        ("MSEdgeHTM", "edge"),
        ("BraveHTML", "brave"),
        ("VivaldiHTM.123", "vivaldi"),
        ("OperaStable", "opera"),
        ("UnknownBrowser", None),
        (None, None),
    ],
)
def test_windows_default_browser_mapping(
    prog_id: str | None, expected: str | None
) -> None:
    assert browser_from_prog_id(prog_id) == expected
