"""Windows-safe filename handling independent of the current platform."""

from __future__ import annotations

import re

_INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\ud800-\udfff]+')
_RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def _validate_replacement(replacement: str) -> None:
    if len(replacement) > 1:
        raise ValueError("replacement deve ter no máximo um caractere")
    if replacement and (
        _INVALID_WINDOWS_CHARS.search(replacement) or replacement in {".", " "}
    ):
        raise ValueError("replacement deve ser válido em nomes de arquivo Windows")


def _truncate_utf16(value: str, max_units: int) -> str:
    """Truncate without splitting a Unicode character's UTF-16 representation."""

    result: list[str] = []
    used_units = 0
    for character in value:
        character_units = 2 if ord(character) > 0xFFFF else 1
        if used_units + character_units > max_units:
            break
        result.append(character)
        used_units += character_units
    return "".join(result)


def sanitize_windows_filename(
    name: str,
    *,
    max_length: int = 240,
    fallback: str = "audio",
    replacement: str = "_",
) -> str:
    """Return a safe Windows filename component without an extension.

    Invalid characters and ASCII controls are replaced, trailing periods and
    spaces are removed, DOS device names are prefixed, and the result is
    limited to ``max_length`` UTF-16 code units. Lone surrogate code points are
    invalid Unicode/Windows filename data and are replaced before truncation.
    """

    if max_length < 1:
        raise ValueError("max_length deve ser maior que zero")
    _validate_replacement(replacement)

    safe = _INVALID_WINDOWS_CHARS.sub(replacement, name).strip().rstrip(". ")
    if not safe:
        safe = _INVALID_WINDOWS_CHARS.sub(replacement, fallback).strip().rstrip(". ")
    if not safe:
        safe = "audio"

    safe = _truncate_utf16(safe, max_length).rstrip(". ")
    if not safe:
        safe = _truncate_utf16("audio", max_length)

    stem = safe.split(".", maxsplit=1)[0].upper()
    if stem in _RESERVED_WINDOWS_NAMES:
        safe = _truncate_utf16(f"_{safe}", max_length).rstrip(". ")

    return safe
