from __future__ import annotations

from pathlib import Path

import pytest

from music_downloader.csv_importer import CsvHeaderError, import_exportify_csv
from music_downloader.text import normalized_dedupe_key


def test_imports_exportify_utf8_bom_and_collapses_whitespace(tmp_path: Path) -> None:
    source = tmp_path / "playlist.csv"
    source.write_text(
        'Track Name,Artist Name(s)\n"  Minha   Música "," Artista  Um "\n',
        encoding="utf-8-sig",
    )

    result = import_exportify_csv(source)

    assert result.queries == ("Minha Música Artista Um",)
    assert result.tracks[0].title == "Minha Música"
    assert result.tracks[0].artist == "Artista Um"
    assert result.tracks[0].source_line == 2
    assert result.encoding == "utf-8-sig"
    assert result.imported_count == 1
    assert result.invalid_count == 0


def test_accepts_localized_headers_and_semicolon_dialect(tmp_path: Path) -> None:
    source = tmp_path / "playlist.csv"
    source.write_text(
        "Nome da música;Artistas\nÁguas de Março;Elis Regina\n",
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.queries == ("Águas de Março Elis Regina",)


def test_falls_back_to_cp1252(tmp_path: Path) -> None:
    source = tmp_path / "playlist.csv"
    source.write_bytes("Track,Artist\nHalo,Beyoncé\n".encode("cp1252"))

    result = import_exportify_csv(source)

    assert result.queries == ("Halo Beyoncé",)
    assert result.encoding == "cp1252"


def test_records_incomplete_and_extra_rows_and_deduplicates(tmp_path: Path) -> None:
    source = tmp_path / "playlist.csv"
    source.write_text(
        "Track,Artist\n"
        "Valid Song,Artist\n"
        ",Artist\n"
        "Missing Artist,\n"
        "valid song,ARTIST\n"
        "Shifted,Artist,unexpected\n",
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.queries == ("Valid Song Artist",)
    assert result.total_rows == 5
    assert result.duplicate_count == 1
    assert result.invalid_count == 3
    assert [row.source_line for row in result.invalid_rows] == [3, 4, 6]
    assert "nome da faixa" in result.invalid_rows[0].reason
    assert "artista" in result.invalid_rows[1].reason
    assert "mais colunas" in result.invalid_rows[2].reason


def test_strict_parser_rejects_text_after_closing_quote_and_recovers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "malformed.csv"
    source.write_text(
        'Track,Artist\n"Broken"junk,Artist\nValid Song,Good Artist\n',
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.total_rows == 2
    assert result.queries == ("Valid Song Good Artist",)
    assert result.invalid_count == 1
    assert result.invalid_rows[0].source_line == 2
    assert "após o fechamento de aspas" in result.invalid_rows[0].reason


def test_unclosed_quote_does_not_consume_following_valid_record(
    tmp_path: Path,
) -> None:
    source = tmp_path / "unclosed.csv"
    source.write_text(
        'Track,Artist\n"Broken,Artist\nValid Song,Good Artist\n',
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.total_rows == 2
    assert result.queries == ("Valid Song Good Artist",)
    assert result.invalid_count == 1
    assert result.invalid_rows[0].source_line == 2
    assert "aspas não fechadas" in result.invalid_rows[0].reason


def test_preserves_valid_commas_and_escaped_quotes(tmp_path: Path) -> None:
    source = tmp_path / "quoted.csv"
    source.write_text(
        'Track,Artist\n"Song, ""Live""","Artist ""DJ"""\n',
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.queries == ('Song, "Live" Artist "DJ"',)
    assert result.invalid_count == 0


def test_rejects_multiline_fields_and_continues_after_them(tmp_path: Path) -> None:
    source = tmp_path / "multiline.csv"
    source.write_text(
        'Track,Artist\n"First line\nsecond line",Artist\nValid,Performer\n',
        encoding="utf-8",
    )

    result = import_exportify_csv(source)

    assert result.total_rows == 3
    assert result.queries == ("Valid Performer",)
    assert [row.source_line for row in result.invalid_rows] == [2, 3]
    assert "multilinha" in result.invalid_rows[0].reason


@pytest.mark.parametrize(
    ("content", "expected_fragments"),
    [
        ("", ("nome da faixa", "artista", "nenhum")),
        ("Album,Year\nExample,2020\n", ("nome da faixa", "artista", "Album", "Year")),
        ("Track,Album\nExample,Album\n", ("artista", "Track", "Album")),
    ],
)
def test_header_error_is_clear(
    tmp_path: Path, content: str, expected_fragments: tuple[str, ...]
) -> None:
    source = tmp_path / "invalid.csv"
    source.write_text(content, encoding="utf-8")

    with pytest.raises(CsvHeaderError) as captured:
        import_exportify_csv(source)

    for fragment in expected_fragments:
        assert fragment in str(captured.value)


def test_real_exportify_sample_has_expected_counts() -> None:
    source = Path(__file__).resolve().parents[1] / "csv-example.csv"

    result = import_exportify_csv(source)

    assert result.total_rows == 159
    assert result.imported_count == 158
    assert result.duplicate_count == 1
    assert result.invalid_count == 0
    assert len({normalized_dedupe_key(query) for query in result.queries}) == 158
