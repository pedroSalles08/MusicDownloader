"""Robust import of Exportify and similar Spotify playlist CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
import re
import unicodedata

from music_downloader.models import CsvImportResult, ImportedTrack, InvalidCsvRow
from music_downloader.text import collapse_whitespace, normalized_dedupe_key

TRACK_HEADER_ALIASES = (
    "Track Name",
    "Track Name(s)",
    "Track",
    "Title",
    "Song",
    "Song Name",
    "Faixa",
    "Nome",
    "Nome da faixa",
    "Nome da música",
    "Música",
    "Título",
)

ARTIST_HEADER_ALIASES = (
    "Artist Name(s)",
    "Artist Name",
    "Artist(s)",
    "Artist",
    "Artists",
    "Performer",
    "Artista",
    "Artistas",
    "Nome do artista",
    "Nome dos artistas",
)

class CsvHeaderError(ValueError):
    """Raised when required track or artist headers cannot be identified."""


def _normalize_header(value: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", without_accents.casefold()).split())


def _find_header(headers: list[str], aliases: tuple[str, ...]) -> str | None:
    normalized_headers = {_normalize_header(header): header for header in headers}
    for alias in aliases:
        match = normalized_headers.get(_normalize_header(alias))
        if match is not None:
            return match
    return None


def _decode_csv(path: Path) -> tuple[str, str]:
    content = path.read_bytes()
    try:
        return content.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        return content.decode("cp1252"), "cp1252"


def _csv_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def _quote_error(record: str, dialect: csv.Dialect) -> str | None:
    """Validate RFC-style quote placement before passing data to ``csv``."""

    delimiter = dialect.delimiter
    quotechar = dialect.quotechar
    escapechar = dialect.escapechar
    # Exportify follows the conventional RFC 4180 doubled-quote escaping. A
    # header without quotes gives ``Sniffer`` no evidence to infer this flag.
    doublequote = True
    state = "field_start"
    index = 0

    while index < len(record):
        character = record[index]

        if escapechar and character == escapechar:
            if index + 1 >= len(record):
                return "caractere de escape sem conteúdo após ele"
            index += 2
            continue

        if state == "field_start":
            if character == delimiter:
                index += 1
                continue
            if quotechar and character == quotechar:
                state = "quoted"
                index += 1
                continue
            state = "unquoted"
            index += 1
            continue

        if state == "unquoted":
            if character == delimiter:
                state = "field_start"
            elif quotechar and character == quotechar:
                return "aspas encontradas no meio de um campo não delimitado"
            index += 1
            continue

        if state == "quoted":
            if quotechar and character == quotechar:
                if (
                    doublequote
                    and index + 1 < len(record)
                    and record[index + 1] == quotechar
                ):
                    index += 2
                    continue
                state = "after_quote"
            index += 1
            continue

        if character == delimiter:
            state = "field_start"
            index += 1
            continue
        return "conteúdo inesperado após o fechamento de aspas"

    if state == "quoted":
        return "aspas não fechadas; campos multilinha não são suportados"
    return None


def _parse_record(record: str, dialect: csv.Dialect) -> list[str]:
    quote_error = _quote_error(record, dialect)
    if quote_error:
        raise csv.Error(quote_error)

    reader = csv.reader([record], dialect=dialect, doublequote=True, strict=True)
    return next(reader)


def _header_error(headers: list[str], track_header: str | None, artist_header: str | None) -> CsvHeaderError:
    missing: list[str] = []
    if track_header is None:
        missing.append("nome da faixa")
    if artist_header is None:
        missing.append("artista")
    found = ", ".join(headers) if headers else "nenhum"
    return CsvHeaderError(
        "Não foi possível identificar a(s) coluna(s) de "
        f"{' e '.join(missing)}. Cabeçalhos encontrados: {found}."
    )


def import_exportify_csv(path: str | Path) -> CsvImportResult:
    """Import a playlist CSV without aborting on incomplete data rows.

    UTF-8 (with or without BOM) is preferred. If strict UTF-8 decoding fails,
    Windows-1252 is used. Required headers are compared case-insensitively and
    without accents or punctuation. Exportify emits one record per physical
    line, so multiline quoted fields are rejected. This lets a malformed quote
    be recorded without consuming the following valid track.
    """

    source = Path(path)
    text, encoding = _decode_csv(source)
    physical_lines = text.splitlines()
    header_record = physical_lines[0] if physical_lines else ""
    dialect = _csv_dialect(header_record)
    try:
        headers = _parse_record(header_record, dialect)
    except csv.Error as error:
        raise CsvHeaderError(f"Cabeçalho CSV malformado na linha 1: {error}.") from error

    track_header = _find_header(headers, TRACK_HEADER_ALIASES)
    artist_header = _find_header(headers, ARTIST_HEADER_ALIASES)
    if track_header is None or artist_header is None:
        raise _header_error(headers, track_header, artist_header)

    tracks: list[ImportedTrack] = []
    invalid_rows: list[InvalidCsvRow] = []
    seen: set[str] = set()
    duplicate_count = 0
    total_rows = 0

    track_index = headers.index(track_header)
    artist_index = headers.index(artist_header)

    for source_line, record in enumerate(physical_lines[1:], start=2):
        total_rows += 1
        try:
            values = _parse_record(record, dialect)
        except csv.Error as error:
            invalid_rows.append(
                InvalidCsvRow(
                    source_line=source_line,
                    reason=f"CSV malformado: {error}",
                )
            )
            continue

        if len(values) > len(headers):
            invalid_rows.append(
                InvalidCsvRow(
                    source_line=source_line,
                    reason="A linha possui mais colunas que o cabeçalho.",
                )
            )
            continue

        title = collapse_whitespace(
            values[track_index] if track_index < len(values) else ""
        )
        artist = collapse_whitespace(
            values[artist_index] if artist_index < len(values) else ""
        )
        missing_values: list[str] = []
        if not title:
            missing_values.append("nome da faixa")
        if not artist:
            missing_values.append("artista")
        if missing_values:
            invalid_rows.append(
                InvalidCsvRow(
                    source_line=source_line,
                    reason=f"Campo(s) vazio(s): {' e '.join(missing_values)}.",
                )
            )
            continue

        track = ImportedTrack(title=title, artist=artist, source_line=source_line)
        key = normalized_dedupe_key(track.query)
        if key in seen:
            duplicate_count += 1
            continue

        seen.add(key)
        tracks.append(track)

    return CsvImportResult(
        tracks=tuple(tracks),
        invalid_rows=tuple(invalid_rows),
        duplicate_count=duplicate_count,
        total_rows=total_rows,
        encoding=encoding,
    )
