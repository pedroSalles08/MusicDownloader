import pytest

from music_downloader.windows_paths import sanitize_windows_filename


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def test_replaces_invalid_characters_and_controls() -> None:
    result = sanitize_windows_filename('Song: Live?\x00')

    assert result == "Song_ Live_"


def test_removes_trailing_periods_and_spaces() -> None:
    assert sanitize_windows_filename("  title...   ") == "title"


@pytest.mark.parametrize("name", ["CON", "con.txt", "LPT9", "aux.MP3"])
def test_avoids_reserved_windows_device_names(name: str) -> None:
    assert sanitize_windows_filename(name).startswith("_")


def test_uses_fallback_when_nothing_remains() -> None:
    assert sanitize_windows_filename("...   ", fallback="sem nome") == "sem nome"


def test_limits_length_and_cleans_new_trailing_period() -> None:
    result = sanitize_windows_filename("abcdefgh...", max_length=10)

    assert result == "abcdefgh"
    assert len(result) <= 10


def test_limits_supplementary_characters_by_utf16_units() -> None:
    result = sanitize_windows_filename("😀" * 128, max_length=255)

    assert result == "😀" * 127
    assert utf16_units(result) == 254


def test_default_limit_allows_only_120_emoji() -> None:
    result = sanitize_windows_filename("😀" * 128)

    assert result == "😀" * 120
    assert utf16_units(result) == 240


def test_never_splits_character_when_one_utf16_unit_remains() -> None:
    result = sanitize_windows_filename("a😀", max_length=2)

    assert result == "a"
    assert utf16_units(result) <= 2


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_replaces_lone_surrogates_safely(surrogate: str) -> None:
    result = sanitize_windows_filename(f"a{surrogate}b")

    assert result == "a_b"
    assert utf16_units(result) == 3


@pytest.mark.parametrize("max_length", [0, -1])
def test_rejects_non_positive_limit(max_length: int) -> None:
    with pytest.raises(ValueError, match="maior que zero"):
        sanitize_windows_filename("title", max_length=max_length)


@pytest.mark.parametrize("replacement", ["xx", ".", "?", " "])
def test_rejects_invalid_replacement(replacement: str) -> None:
    with pytest.raises(ValueError, match="replacement"):
        sanitize_windows_filename("title", replacement=replacement)
