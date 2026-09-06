"""Windows browser detection for yt-dlp cookie authentication."""

from __future__ import annotations

import winreg


COOKIE_BROWSER_LABELS: tuple[tuple[str, str], ...] = (
    ("firefox", "Mozilla Firefox"),
    ("chrome", "Google Chrome"),
    ("edge", "Microsoft Edge"),
    ("brave", "Brave"),
    ("vivaldi", "Vivaldi"),
    ("opera", "Opera"),
)
SUPPORTED_COOKIE_BROWSERS = frozenset(
    browser for browser, _label in COOKIE_BROWSER_LABELS
)


def browser_from_prog_id(prog_id: str | None) -> str | None:
    """Map a Windows HTTPS association ProgId to a yt-dlp browser name."""

    normalized = (prog_id or "").casefold()
    for marker, browser in (
        ("firefox", "firefox"),
        ("chrome", "chrome"),
        ("microsoftedge", "edge"),
        ("msedge", "edge"),
        ("brave", "brave"),
        ("vivaldi", "vivaldi"),
        ("opera", "opera"),
    ):
        if marker in normalized:
            return browser
    return None


def detect_default_cookie_browser() -> str | None:
    """Return the supported browser associated with HTTPS for this Windows user."""

    key_path = (
        r"Software\Microsoft\Windows\Shell\Associations"
        r"\UrlAssociations\https\UserChoice"
    )
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            prog_id, _value_type = winreg.QueryValueEx(key, "ProgId")
    except (OSError, TypeError):
        return None
    return browser_from_prog_id(prog_id if isinstance(prog_id, str) else None)
