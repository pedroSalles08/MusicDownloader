from music_downloader.list_parser import parse_semicolon_list


def test_parses_one_query() -> None:
    result = parse_semicolon_list("Música A - Artista")

    assert result.queries == ("Música A - Artista",)
    assert result.duplicate_count == 0
    assert result.empty_count == 0


def test_trims_ignores_empty_items_and_keeps_order() -> None:
    result = parse_semicolon_list("  Música A  ; ; Música B ;;")

    assert result.queries == ("Música A", "Música B")
    assert result.empty_count == 3


def test_deduplicates_case_and_equivalent_unicode_stably() -> None:
    composed = "Café"
    decomposed = "Cafe\N{COMBINING ACUTE ACCENT}"

    result = parse_semicolon_list(
        f"{composed}; {decomposed}; CAFÉ; Straße; STRASSE; Outra"
    )

    assert result.queries == ("Café", "Straße", "Outra")
    assert result.duplicate_count == 3


def test_empty_input_has_one_ignored_segment() -> None:
    result = parse_semicolon_list("")

    assert result.queries == ()
    assert result.empty_count == 1


def test_keeps_mixed_names_youtube_video_and_playlist_links() -> None:
    video = "https://youtu.be/video-id"
    playlist = "https://www.youtube.com/playlist?list=PL123"

    result = parse_semicolon_list(f"Song Artist; {video}; {playlist}")

    assert result.queries == ("Song Artist", video, playlist)
