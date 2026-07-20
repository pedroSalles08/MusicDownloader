"""Internal text normalization helpers."""

from __future__ import annotations

import unicodedata


def normalized_dedupe_key(value: str) -> str:
    """Normalize compatibility variants and case for stable comparisons."""

    return unicodedata.normalize("NFKC", value).casefold()


def collapse_whitespace(value: str) -> str:
    """Collapse all Unicode whitespace runs and trim their edges."""

    return " ".join(value.split())
