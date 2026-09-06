from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

from PySide6.QtCore import QTimer, Qt

from music_downloader.download_profiles import (
    AUDIO_BITRATE_CHOICES,
    DEFAULT_DOWNLOAD_PROFILE,
    VIDEO_HEIGHT_CHOICES,
    AudioFormat,
    DownloadProfile,
    MediaKind,
    VideoFormat,
)
from music_downloader.models import (
    DownloadBatchResult,
    DownloadProgress,
    DownloadProgressStatus,
    DownloadResult,
    DownloadStatus,
    SearchBatchResult,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from music_downloader.ui.main_window import FlowStage, MainWindow
from music_downloader.ui.styles import ACCENT, BACKGROUND, SURFACE, TEXT_PRIMARY, WARNING


def _as_media_kind(value: object) -> MediaKind:
    return value if isinstance(value, MediaKind) else MediaKind(str(value))


def _as_audio_format(value: object) -> AudioFormat | None:
    if value is None:
        return None
    return value if isinstance(value, AudioFormat) else AudioFormat(str(value))


def _as_video_format(value: object) -> VideoFormat | None:
    if value is None:
        return None
    return value if isinstance(value, VideoFormat) else VideoFormat(str(value))


class FakeSearchService:
    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay
        self.calls: list[tuple[str, ...]] = []

    def search_batch(self, queries, *, cancellation, progress_callback):
        items = tuple(queries)
        self.calls.append(items)
        results = []
        for index, query in enumerate(items, start=1):
            deadline = time.monotonic() + self.delay
            while time.monotonic() < deadline:
                if cancellation.wait(0.005):
                    return SearchBatchResult(tuple(results), True)
            if cancellation.cancelled:
                break
            lowered = query.casefold()
            if "missing" in lowered:
                result = SearchResult(query=query, status=SearchStatus.NO_RESULT)
            elif "search-error" in lowered:
                result = SearchResult(
                    query=query,
                    status=SearchStatus.ERROR,
                    error="OSError: offline",
                )
            else:
                identifier = f"id-{index}-{len(self.calls)}"
                result = SearchResult(
                    query=query,
                    status=SearchStatus.FOUND,
                    title=f"Título de {query}",
                    channel="Canal fake",
                    duration=125,
                    id=identifier,
                    url=f"https://video.example/{identifier}",
                )
            results.append(result)
            progress_callback(SearchProgress(index, len(items), result))
        return SearchBatchResult(tuple(results), cancellation.cancelled)


class FakeDownloadService:
    def __init__(self, delay: float = 0.0, *, preflight_error: str | None = None) -> None:
        self.delay = delay
        self.preflight_error = preflight_error
        self.calls: list[dict[str, object]] = []

    def download_batch(
        self,
        approved_results,
        output_directory,
        *,
        profile,
        embed_thumbnail,
        aria2c_path,
        cookie_browser,
        cancellation,
        progress_callback,
    ):
        items = tuple(approved_results)
        self.calls.append(
            {
                "items": items,
                "output_directory": str(output_directory),
                "profile": profile,
                "embed_thumbnail": embed_thumbnail,
                "aria2c_path": aria2c_path,
                "cookie_browser": cookie_browser,
            }
        )
        if self.preflight_error:
            return DownloadBatchResult((), False, self.preflight_error)
        results = []
        for index, item in enumerate(items, start=1):
            progress_callback(
                DownloadProgress(
                    query=item.query,
                    id=item.id,
                    item_index=index,
                    total_items=len(items),
                    processed_items=index - 1,
                    status=DownloadProgressStatus.DOWNLOADING,
                    item_fraction=0.25,
                )
            )
            deadline = time.monotonic() + self.delay
            while time.monotonic() < deadline:
                if cancellation.wait(0.005):
                    return DownloadBatchResult(tuple(results), True)
            if cancellation.cancelled:
                break
            if "fail" in item.query.casefold():
                outcome = DownloadResult(
                    query=item.query,
                    id=item.id,
                    status=DownloadStatus.ERROR,
                    output_path=None,
                    attempts=1,
                    error="RuntimeError: fake failure",
                )
                progress_status = DownloadProgressStatus.ERROR
            else:
                outcome = DownloadResult(
                    query=item.query,
                    id=item.id,
                    status=DownloadStatus.COMPLETED,
                    output_path=Path(output_directory) / f"{item.id}.mp3",
                    attempts=1,
                )
                progress_status = DownloadProgressStatus.COMPLETED
            results.append(outcome)
            progress_callback(
                DownloadProgress(
                    query=item.query,
                    id=item.id,
                    item_index=index,
                    total_items=len(items),
                    processed_items=index,
                    status=progress_status,
                    item_fraction=1.0,
                )
            )
        return DownloadBatchResult(tuple(results), cancellation.cancelled)


def make_window(
    qtbot,
    *,
    search_delay: float = 0.0,
    download_delay: float = 0.0,
    download_service=None,
):
    search = FakeSearchService(search_delay)
    download = download_service or FakeDownloadService(download_delay)
    window = MainWindow(
        search_service=search,
        download_service=download,
        executable_resolver=lambda name: "aria2c.exe" if name == "aria2c" else None,
    )
    qtbot.addWidget(window)
    window.show()
    return window, search, download


def wait_idle(qtbot, window: MainWindow, timeout: int = 3000) -> None:
    qtbot.waitUntil(lambda: not window.is_busy, timeout=timeout)


def prepare_review(qtbot, window: MainWindow, text: str = "One; Two") -> None:
    window.input_edit.setPlainText(text)
    window.prepare_and_search()
    wait_idle(qtbot, window)
    assert window.stage is FlowStage.REVIEW


def test_window_starts_with_native_progressive_add_page(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    assert window.isVisible()
    assert window.windowTitle() == "Music Downloader"
    assert window.minimumSize().width() == 720
    assert window.stage is FlowStage.ADD
    assert window.shell.stack.currentWidget() is window.add_page
    assert window.add_page.isVisible()
    assert not window.review_page.isVisible()
    assert not (window.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert window.input_edit.placeholderText()
    assert window.add_page.search_button.text() == "Pesquisar músicas"


def test_import_and_options_are_discrete_popovers(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    window._show_import_popover()
    assert window.import_popover.isVisible()
    assert window.import_popover.csv_button.text().startswith("Importar arquivo CSV")
    window.import_popover.hide()

    window._show_options_from_add()
    assert window.options_popover.isVisible()
    assert window.cover_checkbox.text() == "Incorporar thumbnail como capa"
    assert window.cookie_browser_combo.count() >= 2


def test_real_csv_import_preserves_summary_and_deduplication(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    sample = Path(__file__).resolve().parents[1] / "csv-example.csv"
    window.input_edit.setPlainText("Save a Prayer Duran Duran")

    result = window.import_csv_path(sample)

    assert result is not None
    assert result.total_rows == 159
    parsed = window.input_edit.toPlainText().split("; ")
    assert parsed.count("Save a Prayer Duran Duran") == 1
    assert len(parsed) == 158
    assert "CSV:" in window.last_notice


def test_spotify_popover_guidance_does_not_block_typed_list(qtbot) -> None:
    window, search, _download = make_window(qtbot)
    window.spotify_edit.setText("https://open.spotify.com/playlist/abc123")
    window.input_edit.setPlainText("Valid Song Artist")

    assert window.process_spotify_text()
    assert "Exportify" in window.spotify_hint_label.text()
    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert search.calls == [("Valid Song Artist",)]
    assert window.review_model.rowCount() == 1


def test_empty_and_duplicate_parser_states_are_preserved(qtbot) -> None:
    window, search, _download = make_window(qtbot)

    window.prepare_and_search()
    assert "Nenhuma música válida" in window.last_notice
    assert window.stage is FlowStage.ADD

    window.input_edit.setPlainText("One; one;; Two")
    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert search.calls == [("One", "Two")]
    assert window.last_parse_result is not None
    assert window.last_parse_result.duplicate_count == 1
    assert window.last_parse_result.empty_count == 1


def test_search_page_is_minimal_and_event_loop_stays_responsive(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.25)
    window.input_edit.setPlainText("Slow Song")
    ticked: list[bool] = []

    window.prepare_and_search()
    assert window.stage is FlowStage.SEARCHING
    assert window.search_page.isVisible()
    assert window.search_page.activity.maximum() == 0
    assert window.search_page.cancel_button.isEnabled()
    QTimer.singleShot(30, lambda: ticked.append(True))
    qtbot.waitUntil(lambda: bool(ticked), timeout=500)

    assert window.is_busy
    wait_idle(qtbot, window)
    assert window.stage is FlowStage.REVIEW


def test_successful_search_transitions_to_list_and_dynamic_cta(qtbot, tmp_path: Path) -> None:
    window, _search, _download = make_window(qtbot)
    prepare_review(qtbot, window, "One; Two")

    assert window.review_model.rowCount() == 2
    assert [result.query for result in window.search_results] == ["One", "Two"]
    assert window.review_model.selected_count == 2
    assert "2 encontradas" in window.review_page.summary_label.text()
    assert window.download_button.text() == "Baixar 2 áudios em MP3 · 192 kbps"
    assert not window.download_button.isEnabled()

    window.destination_edit.setText(str(tmp_path))
    assert window.download_button.isEnabled()
    window.review_model.setData(
        window.review_model.index(1),
        Qt.CheckState.Unchecked,
        Qt.ItemDataRole.CheckStateRole,
    )
    assert window.download_button.text() == "Baixar 1 áudio em MP3 · 192 kbps"


def test_playlist_expansion_preserves_order_url_and_individual_research(qtbot) -> None:
    class PlaylistSearchService:
        def __init__(self) -> None:
            self.calls = []

        def search_batch(self, queries, *, cancellation, progress_callback):
            query = tuple(queries)[0]
            self.calls.append(query)
            if "playlist?" in query:
                results = tuple(
                    SearchResult(
                        query=f"https://www.youtube.com/watch?v={identifier}",
                        status=SearchStatus.FOUND,
                        title=title,
                        id=identifier,
                        url=f"https://www.youtube.com/watch?v={identifier}",
                    )
                    for identifier, title in (("one", "Track one"), ("two", "Track two"))
                )
            else:
                identifier = query.rsplit("=", 1)[-1]
                results = (
                    SearchResult(
                        query=query,
                        status=SearchStatus.FOUND,
                        title=f"Researched {identifier}",
                        id=identifier,
                        url=query,
                    ),
                )
            for result in results:
                progress_callback(SearchProgress(1, 1, result))
            return SearchBatchResult(results, cancellation.cancelled)

    search = PlaylistSearchService()
    window = MainWindow(search_service=search, download_service=FakeDownloadService())
    qtbot.addWidget(window)
    window.show()
    playlist_url = "https://www.youtube.com/playlist?list=PL123"
    window.input_edit.setPlainText(playlist_url)

    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert [result.title for result in window.search_results] == ["Track one", "Track two"]
    assert [result.id for result in window.search_results] == ["one", "two"]
    assert window.review_model.selected_count == 2

    window.review_list.setCurrentIndex(window.review_model.index(0))
    window.research_current_row()
    wait_idle(qtbot, window)

    assert search.calls[-1] == "https://www.youtube.com/watch?v=one"
    assert window.search_results[0].title == "Researched one"
    assert window.search_results[1].title == "Track two"


def test_inline_edit_researches_and_restores_selection(qtbot) -> None:
    window, search, _download = make_window(qtbot)
    prepare_review(qtbot, window, "Original")
    index = window.review_model.index(0)

    window._open_editor(index)
    assert window.review_page.editor.isVisible()
    window.review_page.query_edit.setText("Edited Query")
    window.research_from_editor()
    wait_idle(qtbot, window)

    assert search.calls[-1] == ("Edited Query",)
    assert window.search_results[0].query == "Edited Query"
    assert window.search_results[0].title == "Título de Edited Query"
    assert window.review_model.selected_count == 1


def test_review_selection_supports_keyboard_and_context_menu(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    prepare_review(qtbot, window, "One; Two")
    index = window.review_model.index(0)
    window.review_list.setCurrentIndex(index)
    window.review_list.setFocus()

    qtbot.keyClick(window.review_list, Qt.Key.Key_Space)

    assert window.review_model.selected_count == 1
    assert (
        window.review_list.contextMenuPolicy()
        is Qt.ContextMenuPolicy.CustomContextMenu
    )
    assert window.review_page.more_button.isEnabled()


def test_download_uses_approved_results_options_and_shows_minimal_completion(
    qtbot, tmp_path: Path
) -> None:
    window, _search, download = make_window(qtbot)
    prepare_review(qtbot, window, "Good Song; Fail Song")
    window.destination_edit.setText(str(tmp_path))
    window.cover_checkbox.setChecked(True)
    window.cookie_browser_combo.setCurrentIndex(
        window.cookie_browser_combo.findData("chrome")
    )

    window.start_download()
    assert window.stage is FlowStage.DOWNLOADING
    wait_idle(qtbot, window)

    call = download.calls[0]
    assert [result.query for result in call["items"]] == ["Good Song", "Fail Song"]
    assert call["profile"] == DEFAULT_DOWNLOAD_PROFILE
    assert call["embed_thumbnail"] is True
    assert call["aria2c_path"] == "aria2c.exe"
    assert call["cookie_browser"] == "chrome"
    assert window.stage is FlowStage.COMPLETE
    assert window.completion_page.title_label.text() == "Download finalizado"
    assert "1 áudio foi baixado" in window.completion_page.summary_label.text()
    assert "1 áudio não foi concluído" in window.completion_page.failures_button.text()
    assert "fake failure" in window.completion_page.failures_edit.toPlainText()


def test_preflight_error_returns_to_review_with_actionable_notice(qtbot, tmp_path: Path) -> None:
    download = FakeDownloadService(preflight_error="FFmpeg ausente")
    window, _search, _download = make_window(qtbot, download_service=download)
    prepare_review(qtbot, window, "One")
    window.destination_edit.setText(str(tmp_path))

    window.start_download()
    wait_idle(qtbot, window)

    assert window.stage is FlowStage.REVIEW
    assert "FFmpeg ausente" in window.review_page.notice.text()
    assert window.review_model.selected_count == 1


def test_download_progress_is_monotonic_and_ignores_late_terminal_events(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    result = SearchResult(
        query="Song",
        status=SearchStatus.FOUND,
        title="Song title",
        id="id",
        url="https://video.example/id",
    )
    window.review_model.reset_results((result,))
    generation = window._next_generation()
    window._download_rows = [0]
    window._download_items = [result]
    window._download_terminal = False
    window.download_page.reset(1)

    def progress(fraction: float, status=DownloadProgressStatus.DOWNLOADING):
        return DownloadProgress(
            query="Song",
            id="id",
            item_index=1,
            total_items=1,
            processed_items=1 if status is DownloadProgressStatus.COMPLETED else 0,
            status=status,
            item_fraction=fraction,
        )

    window._on_download_progress(generation, progress(0.75))
    window._on_download_progress(generation, progress(0.25))
    assert window.total_progress.value() == 75

    window._on_download_progress(
        generation, progress(1.0, DownloadProgressStatus.COMPLETED)
    )
    window._on_download_progress(generation, progress(0.9))
    assert window.review_model.data(window.review_model.index(0), window.review_model.StatusRole) == "Concluído"
    assert window.total_progress.value() == 100


def test_search_results_are_ordered_and_post_terminal_callbacks_are_ignored(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._search_queries = ("A", "B")
    window._search_received = {}
    window._search_terminal = False
    window._search_target_row = None
    window.review_model.reset_waiting(window._search_queries)
    result_a = SearchResult(query="A", status=SearchStatus.FOUND, title="Title A", id="a", url="https://video/a")
    result_b = SearchResult(query="B", status=SearchStatus.FOUND, title="Title B", id="b", url="https://video/b")

    window._on_search_progress(generation, SearchProgress(2, 2, result_b))
    window._on_search_progress(generation, SearchProgress(1, 2, result_a))
    window._on_search_completed(
        generation, SearchBatchResult((result_b, result_a), False)
    )

    assert [result.query for result in window.search_results] == ["A", "B"]
    late = SearchResult(query="A", status=SearchStatus.FOUND, title="Late", id="late", url="https://video/late")
    window._on_search_progress(generation, SearchProgress(1, 2, late))
    assert window.search_results[0].title == "Title A"


def test_new_search_rejects_previous_generation(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.12)
    window.input_edit.setPlainText("First")
    window.prepare_and_search()
    old_generation = window._active_generation
    wait_idle(qtbot, window)

    window.input_edit.setPlainText("Second")
    window.prepare_and_search()
    assert window._active_generation != old_generation
    old_result = SearchResult(query="First", status=SearchStatus.FOUND, title="Old late", id="old", url="https://video/old")
    window._on_search_progress(old_generation, SearchProgress(1, 1, old_result))

    assert window.search_results[0].query == "Second"
    wait_idle(qtbot, window)
    assert window.search_results[0].title == "Título de Second"


def test_download_cancel_keeps_worker_and_close_semantics(qtbot, tmp_path: Path) -> None:
    window, _search, _download = make_window(qtbot, download_delay=0.3)
    prepare_review(qtbot, window, "Slow Download")
    window.destination_edit.setText(str(tmp_path))

    window.start_download()
    assert window.is_busy
    assert window.download_page.cancel_button.isEnabled()
    window.download_page.cancel_button.click()
    wait_idle(qtbot, window)

    assert window.last_download_batch is not None
    assert window.last_download_batch.cancelled
    assert window.stage is FlowStage.COMPLETE


def test_close_during_worker_waits_for_safe_cancellation(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.3)
    window.input_edit.setPlainText("Slow Close")
    window.prepare_and_search()
    assert window.is_busy

    window.close()

    assert window.is_busy
    qtbot.waitUntil(lambda: window._active_thread is None, timeout=3000)
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=1000)


def test_new_operation_returns_to_add_without_discarding_current_fields(qtbot, tmp_path: Path) -> None:
    window, _search, _download = make_window(qtbot)
    prepare_review(qtbot, window, "Keep Me")
    window.destination_edit.setText(str(tmp_path))
    window.start_download()
    wait_idle(qtbot, window)

    window.start_new_operation()

    assert window.stage is FlowStage.ADD
    assert window.input_edit.toPlainText() == "Keep Me"
    assert window.destination_edit.text() == str(tmp_path)


def test_open_folder_uses_desktop_service(qtbot, tmp_path: Path, monkeypatch) -> None:
    window, _search, _download = make_window(qtbot)
    opened: list[str] = []
    monkeypatch.setattr(
        "music_downloader.ui.main_window.QDesktopServices.openUrl",
        lambda url: opened.append(url.toLocalFile()) or True,
    )
    window.destination_edit.setText(str(tmp_path))

    assert window.open_destination_folder()
    assert [Path(value) for value in opened] == [tmp_path]


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_visual_tokens_resources_and_accessibility(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    assert _contrast(TEXT_PRIMARY, BACKGROUND) >= 4.5
    assert _contrast(ACCENT, BACKGROUND) >= 4.5
    assert _contrast(WARNING, SURFACE) >= 4.5
    assert not window.input_edit.accessibleName() == ""
    assert not window.destination_edit.accessibleName() == ""
    assert not window.review_list.accessibleName() == ""
    assert not window.log_edit.accessibleName() == ""
    assert not window.total_progress.accessibleName() == ""
    assert not window.review_delegate._music_icon.isNull()
    assert window.media_kind_combo.accessibleName() == "Tipo de mídia"
    assert window.audio_format_combo.accessibleName() == "Formato de áudio"
    assert window.audio_quality_combo.accessibleName() == "Qualidade do áudio"
    assert window.video_format_combo.accessibleName() == "Formato de vídeo"
    assert window.video_resolution_combo.accessibleName() == "Resolução máxima do vídeo"
    assert window.cover_checkbox.accessibleName() == "Incorporar thumbnail como capa"
    assert window.cookie_browser_combo.accessibleName() == "Sessão do YouTube"


def test_default_visual_produces_default_download_profile(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    assert window.current_download_profile() == DEFAULT_DOWNLOAD_PROFILE
    assert _as_media_kind(window.media_kind_combo.currentData()) == MediaKind.AUDIO
    assert _as_audio_format(window.audio_format_combo.currentData()) == AudioFormat.MP3
    assert int(window.audio_quality_combo.currentData()) == 192
    assert not window.options_popover.audio_container.isHidden()
    assert window.options_popover.video_container.isHidden()


def test_combobox_items_store_correct_enums_and_values(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    kinds = [_as_media_kind(window.media_kind_combo.itemData(i)) for i in range(window.media_kind_combo.count())]
    assert kinds == [MediaKind.AUDIO, MediaKind.VIDEO]

    audio_formats = [
        _as_audio_format(window.audio_format_combo.itemData(i)) for i in range(window.audio_format_combo.count())
    ]
    assert set(audio_formats) == set(AudioFormat)

    audio_bitrates = [
        int(window.audio_quality_combo.itemData(i)) for i in range(window.audio_quality_combo.count())
    ]
    assert audio_bitrates == list(AUDIO_BITRATE_CHOICES)

    video_formats = [
        _as_video_format(window.video_format_combo.itemData(i)) for i in range(window.video_format_combo.count())
    ]
    assert set(video_formats) == set(VideoFormat)

    video_heights = [
        int(window.video_resolution_combo.itemData(i)) if window.video_resolution_combo.itemData(i) is not None else None
        for i in range(window.video_resolution_combo.count())
    ]
    assert video_heights == [None, *sorted(VIDEO_HEIGHT_CHOICES, reverse=True)]


def test_lossy_audio_shows_bitrate_and_produces_chosen_profile(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    window.options_popover.set_profile(
        DownloadProfile.for_audio(AudioFormat.AAC, bitrate_kbps=256)
    )
    assert window.current_download_profile() == DownloadProfile.for_audio(
        AudioFormat.AAC, bitrate_kbps=256
    )
    assert not window.options_popover.audio_quality_widget.isHidden()
    assert window.options_popover.audio_lossless_widget.isHidden()

    window.options_popover.set_profile(
        DownloadProfile.for_audio(AudioFormat.OPUS, bitrate_kbps=320)
    )
    assert window.current_download_profile() == DownloadProfile.for_audio(
        AudioFormat.OPUS, bitrate_kbps=320
    )


def test_lossless_audio_hides_bitrate_and_does_not_send_bitrate(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    for lossless_format in (AudioFormat.FLAC, AudioFormat.ALAC, AudioFormat.WAV):
        window.options_popover.set_profile(DownloadProfile.for_audio(lossless_format))
        profile = window.current_download_profile()

        assert profile == DownloadProfile.for_audio(lossless_format)
        assert profile.audio_bitrate_kbps is None
        assert window.options_popover.audio_quality_widget.isHidden()
        assert not window.options_popover.audio_lossless_widget.isHidden()
        assert "não recupera qualidade" in window.options_popover.audio_lossless_help_label.text()


def test_video_produces_correct_format_and_resolution(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    cases = [
        (
            DownloadProfile.for_video(VideoFormat.MP4_COMPATIBLE, max_height=1080),
            "H.264/AAC",
        ),
        (
            DownloadProfile.for_video(VideoFormat.MP4_FAST, max_height=None),
            "Evita recodificação",
        ),
        (
            DownloadProfile.for_video(VideoFormat.WEBM, max_height=720),
            "WebM",
        ),
        (
            DownloadProfile.for_video(VideoFormat.ORIGINAL, max_height=None),
            "extensão pode variar",
        ),
    ]
    for profile, expected_hint_keyword in cases:
        window.options_popover.set_profile(profile)
        assert window.current_download_profile() == profile
        assert expected_hint_keyword in window.options_popover.video_help_label.text()
        if profile.video_format is VideoFormat.ORIGINAL:
            assert window.options_popover.video_resolution_widget.isHidden()
        else:
            assert not window.options_popover.video_resolution_widget.isHidden()


def test_wav_and_original_uncheck_and_disable_thumbnail(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    # 1. WAV disables and unchecks thumbnail
    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.MP3, bitrate_kbps=192))
    window.cover_checkbox.setChecked(True)
    assert window.cover_checkbox.isChecked()

    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.WAV))
    assert not window.cover_checkbox.isChecked()
    assert not window.cover_checkbox.isEnabled()
    assert "não é suportada" in window.cover_checkbox.toolTip()

    # 2. Original video disables and unchecks thumbnail
    window.options_popover.set_profile(
        DownloadProfile.for_video(VideoFormat.MP4_COMPATIBLE, max_height=1080)
    )
    assert window.cover_checkbox.isEnabled()
    window.cover_checkbox.setChecked(True)

    window.options_popover.set_profile(DownloadProfile.for_video(VideoFormat.ORIGINAL))
    assert not window.cover_checkbox.isChecked()
    assert not window.cover_checkbox.isEnabled()


def test_thumbnail_re_enabled_without_auto_checking(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.WAV))
    assert not window.cover_checkbox.isChecked()
    assert not window.cover_checkbox.isEnabled()

    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.MP3, bitrate_kbps=192))
    assert window.cover_checkbox.isEnabled()
    assert not window.cover_checkbox.isChecked()


def test_popover_uses_available_height_before_requiring_scroll(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    popover = window.options_popover
    popover.set_profile(
        DownloadProfile.for_video(VideoFormat.MP4_COMPATIBLE, max_height=1080)
    )

    popover.show_for(window.add_page.options_button)
    qtbot.waitUntil(popover.isVisible)

    available_height = window.add_page.options_button.screen().availableGeometry().height()
    assert popover.scroll_area.height() == min(
        popover.scroll_content.sizeHint().height(),
        max(280, available_height - 40),
    )
    popover.hide()


def test_invalid_programmatic_profile_is_actionable_and_does_not_start(
    qtbot, tmp_path: Path
) -> None:
    window, _search, download = make_window(qtbot)
    prepare_review(qtbot, window, "One")
    window.destination_edit.setText(str(tmp_path))
    window.media_kind_combo.addItem("Inválido", "invalid-media-kind")

    window.media_kind_combo.setCurrentIndex(window.media_kind_combo.count() - 1)

    assert not window.download_button.isEnabled()
    assert window.download_button.text() == "Configuração de formato inválida"
    window.start_download()
    assert download.calls == []
    assert window.stage is FlowStage.REVIEW
    assert "Configuração de formato inválida" in window.review_page.notice.text()


def test_start_download_forwards_chosen_profile(qtbot, tmp_path: Path) -> None:
    window, _search, download = make_window(qtbot)
    prepare_review(qtbot, window, "Video Item")
    window.destination_edit.setText(str(tmp_path))

    video_profile = DownloadProfile.for_video(VideoFormat.WEBM, max_height=720)
    window.options_popover.set_profile(video_profile)

    window.start_download()
    assert window.stage is FlowStage.DOWNLOADING
    wait_idle(qtbot, window)

    call = download.calls[0]
    assert call["profile"] == video_profile
    assert window.stage is FlowStage.COMPLETE
    assert "1 vídeo foi baixado" in window.completion_page.summary_label.text()


def test_completion_uses_profile_frozen_when_batch_started(
    qtbot, tmp_path: Path
) -> None:
    window, _search, _download = make_window(qtbot, download_delay=0.15)
    prepare_review(qtbot, window, "Video Item")
    window.destination_edit.setText(str(tmp_path))
    window.options_popover.set_profile(
        DownloadProfile.for_video(VideoFormat.WEBM, max_height=720)
    )

    window.start_download()
    window.options_popover.set_profile(
        DownloadProfile.for_audio(AudioFormat.MP3, bitrate_kbps=192)
    )
    wait_idle(qtbot, window)

    assert "1 vídeo foi baixado" in window.completion_page.summary_label.text()


def test_review_cta_formatting_audio_and_video(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    prepare_review(qtbot, window, "One; Two; Three")

    # Audio lossy 1 & 2 items
    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.MP3, bitrate_kbps=192))
    window.review_model.select_all_found()
    assert window.download_button.text() == "Baixar 3 áudios em MP3 · 192 kbps"

    window.review_model.clear_selection()
    window.review_model.setData(
        window.review_model.index(0), Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole
    )
    assert window.download_button.text() == "Baixar 1 áudio em MP3 · 192 kbps"

    # Audio lossless
    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.FLAC))
    assert window.download_button.text() == "Baixar 1 áudio em FLAC"
    window.review_model.select_all_found()
    assert window.download_button.text() == "Baixar 3 áudios em FLAC"

    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.WAV))
    assert window.download_button.text() == "Baixar 3 áudios em WAV"

    # Video with resolution limit
    window.options_popover.set_profile(
        DownloadProfile.for_video(VideoFormat.MP4_COMPATIBLE, max_height=1080)
    )
    assert window.download_button.text() == "Baixar 3 vídeos em MP4 · até 1080p"

    # Video original
    window.options_popover.set_profile(DownloadProfile.for_video(VideoFormat.ORIGINAL))
    assert window.download_button.text() == "Baixar 3 vídeos no formato original"

    # Zero items selected
    window.review_model.clear_selection()
    assert window.download_button.text() == "Baixar vídeos"
    window.options_popover.set_profile(DownloadProfile.for_audio(AudioFormat.MP3))
    assert window.download_button.text() == "Baixar áudios"


def test_all_popover_controls_disabled_when_busy(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    window._set_busy(True)
    assert not window.media_kind_combo.isEnabled()
    assert not window.audio_format_combo.isEnabled()
    assert not window.audio_quality_combo.isEnabled()
    assert not window.video_format_combo.isEnabled()
    assert not window.video_resolution_combo.isEnabled()
    assert not window.cover_checkbox.isEnabled()
    assert not window.cookie_browser_combo.isEnabled()

    window._set_busy(False)
    assert window.media_kind_combo.isEnabled()
    assert window.audio_format_combo.isEnabled()
    assert window.audio_quality_combo.isEnabled()
    assert window.cover_checkbox.isEnabled()
    assert window.cookie_browser_combo.isEnabled()


def test_search_worker_error_uses_feminine_grammar_and_visible_notice(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._search_terminal = False

    window._on_worker_failed("RuntimeError: boom", generation, "search")

    assert "Pesquisa interrompida por erro inesperado" in window.last_notice
    assert window.stage is FlowStage.ADD
    assert window.add_page.notice.isVisible()


def test_module_smoke_test_subprocess() -> None:
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"

    completed = subprocess.run(
        [sys.executable, "-m", "music_downloader", "--smoke-test"],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
