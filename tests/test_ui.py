from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

from PySide6.QtCore import QTimer, Qt

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
from music_downloader.ui.main_window import MainWindow
from music_downloader.ui.styles import BLUE, CREAM, PAPER, WARNING


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
    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay
        self.calls: list[dict[str, object]] = []

    def download_batch(
        self,
        approved_results,
        output_directory,
        *,
        embed_thumbnail,
        aria2c_path,
        cancellation,
        progress_callback,
    ):
        items = tuple(approved_results)
        self.calls.append(
            {
                "items": items,
                "output_directory": str(output_directory),
                "embed_thumbnail": embed_thumbnail,
                "aria2c_path": aria2c_path,
            }
        )
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


def make_window(qtbot, *, search_delay: float = 0.0, download_delay: float = 0.0):
    search = FakeSearchService(search_delay)
    download = FakeDownloadService(download_delay)
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


def test_window_starts_offscreen_with_retro_header_and_status(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    assert window.isVisible()
    assert "Music Downloader" in window.windowTitle()
    assert window.minimumWidth() == 900
    assert "Pronto" in window.statusBar().currentMessage()
    assert window.findChild(type(window.summary_label), "summaryLabel") is not None


def test_real_csv_method_imports_and_deduplicates_against_input(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    sample = Path(__file__).resolve().parents[1] / "csv-example.csv"
    window.input_edit.setPlainText("Save a Prayer - 2009 Remaster Duran Duran")

    result = window.import_csv_path(sample)

    assert result is not None
    assert result.imported_count == 158
    assert "158 importadas" in window.last_notice
    prepared = window.input_edit.toPlainText().split("; ")
    assert len(prepared) == 158
    assert "1 já estavam na lista" in window.last_notice


def test_spotify_fallback_does_not_block_valid_typed_list(qtbot) -> None:
    window, search, _download = make_window(qtbot)
    window.spotify_edit.setText("https://open.spotify.com/playlist/abc123")
    window.input_edit.setPlainText("Valid Song Artist")

    assert window.process_spotify_text()
    assert "Exportify" in window.spotify_hint_label.text()
    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert search.calls == [("Valid Song Artist",)]
    assert window.review_table.rowCount() == 1


def test_empty_and_duplicate_parser_states_are_reflected(qtbot) -> None:
    window, search, _download = make_window(qtbot)

    window.prepare_and_search()
    assert "Nenhuma música válida" in window.last_notice
    assert not window.is_busy

    window.input_edit.setPlainText("One; one;; Two")
    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert search.calls == [("One", "Two")]
    assert window.last_parse_result is not None
    assert window.last_parse_result.duplicate_count == 1
    assert window.last_parse_result.empty_count == 1


def test_ui_event_loop_remains_responsive_during_slow_search(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.25)
    window.input_edit.setPlainText("Slow Song")
    ticked: list[bool] = []

    window.prepare_and_search()
    assert window.is_busy
    assert not window.search_button.isEnabled()
    assert window.cancel_button.isEnabled()
    QTimer.singleShot(30, lambda: ticked.append(True))
    qtbot.waitUntil(lambda: bool(ticked), timeout=500)

    assert window.is_busy
    wait_idle(qtbot, window)


def test_review_selection_edit_and_row_research(qtbot) -> None:
    window, search, _download = make_window(qtbot)
    window.input_edit.setPlainText("Found One; missing song; search-error song")
    window.prepare_and_search()
    wait_idle(qtbot, window)

    assert window.review_table.rowCount() == 3
    assert window.review_table.item(0, 0).checkState() == Qt.CheckState.Checked
    assert window.review_table.item(1, 5).text() == "Sem resultado"
    assert window.review_table.item(2, 5).text() == "Erro"

    window.clear_selection()
    assert not window.download_button.isEnabled()
    window.select_all_found()
    assert window.download_button.isEnabled()

    window.review_table.setCurrentCell(0, 1)
    window.review_table.item(0, 1).setText("Edited Query")
    assert window.review_table.item(0, 5).text().startswith("Editado")
    assert not window.download_button.isEnabled()
    window.research_current_row()
    wait_idle(qtbot, window)

    assert search.calls[-1] == ("Edited Query",)
    assert window.search_results[0].status is SearchStatus.FOUND
    assert window.review_table.item(0, 2).text() == "Título de Edited Query"


def test_download_progress_failure_and_summary(qtbot, tmp_path: Path) -> None:
    window, _search, download = make_window(qtbot)
    window.input_edit.setPlainText("Good Song; Fail Song")
    window.prepare_and_search()
    wait_idle(qtbot, window)
    window.destination_edit.setText(str(tmp_path))
    window.cover_checkbox.setChecked(True)

    window.start_download()
    wait_idle(qtbot, window)

    assert download.calls[0]["embed_thumbnail"] is True
    assert download.calls[0]["aria2c_path"] == "aria2c.exe"
    assert window.last_download_batch is not None
    assert window.last_download_batch.successful_count == 1
    assert window.last_download_batch.failed_count == 1
    assert "1 sucesso" in window.summary_label.text()
    assert "1 falha" in window.summary_label.text()
    assert str(tmp_path) in window.summary_label.text()
    assert window.review_table.item(0, 6).text() == "100%"
    assert window.review_table.item(1, 5).text() == "Falha"
    assert "fake failure" in window.log_edit.toPlainText()


def test_terminal_item_progress_does_not_double_count_total(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._download_rows = [0, 1]
    window._download_terminal = False
    window.review_table.setRowCount(2)

    window._on_download_progress(
        generation,
        DownloadProgress(
            query="first",
            id="one",
            item_index=1,
            total_items=2,
            processed_items=1,
            status=DownloadProgressStatus.COMPLETED,
            item_fraction=1.0,
        )
    )

    assert window.total_progress.value() == 50


def test_download_progress_is_monotonic_and_terminal_item_ignores_late_event(
    qtbot,
) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._download_rows = [0]
    window._download_terminal = False
    window._set_result_at_row(
        0,
        SearchResult(
            query="Song",
            status=SearchStatus.FOUND,
            id="id",
            url="https://video.example/id",
        ),
    )

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
    assert window.review_table.item(0, 5).text() == "Concluído"
    window._on_download_progress(generation, progress(0.9))
    assert window.review_table.item(0, 5).text() == "Concluído"
    assert window.total_progress.value() == 100


def test_download_callback_after_batch_completion_is_ignored(qtbot, tmp_path: Path) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window.destination_edit.setText(str(tmp_path))
    window._download_rows = [0]
    window._download_terminal = False
    window._set_result_at_row(
        0,
        SearchResult(
            query="Song",
            status=SearchStatus.FOUND,
            id="id",
            url="https://video.example/id",
        ),
    )
    outcome = DownloadResult(
        query="Song",
        id="id",
        status=DownloadStatus.COMPLETED,
        output_path=tmp_path / "song.mp3",
        attempts=1,
    )

    window._on_download_completed(
        generation, DownloadBatchResult((outcome,), False)
    )
    window._on_download_progress(
        generation,
        DownloadProgress(
            query="Song",
            id="id",
            item_index=1,
            total_items=1,
            processed_items=0,
            status=DownloadProgressStatus.DOWNLOADING,
            item_fraction=0.1,
        )
    )

    assert window.review_table.item(0, 5).text() == "Concluído"
    assert window.total_progress.value() == 100


def test_search_progress_is_ordered_monotonic_and_ignores_post_terminal(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._search_queries = ("A", "B")
    window._search_received = {}
    window._search_terminal = False
    window._search_max_processed = 0
    window._search_target_row = None
    for row, query in enumerate(window._search_queries):
        window._set_result_at_row(
            row, SearchResult(query=query, status=SearchStatus.NO_RESULT)
        )
    result_a = SearchResult(
        query="A",
        status=SearchStatus.FOUND,
        title="Title A",
        id="a",
        url="https://video.example/a",
    )
    result_b = SearchResult(
        query="B",
        status=SearchStatus.FOUND,
        title="Title B",
        id="b",
        url="https://video.example/b",
    )

    window._on_search_progress(generation, SearchProgress(2, 2, result_b))
    window._on_search_progress(generation, SearchProgress(1, 2, result_a))
    assert window.total_progress.value() == 100
    assert [window.review_table.item(row, 1).text() for row in range(2)] == ["A", "B"]

    window._on_search_completed(
        generation, SearchBatchResult((result_b, result_a), False)
    )
    assert [result.query for result in window.search_results] == ["A", "B"]
    late = SearchResult(
        query="A",
        status=SearchStatus.FOUND,
        title="Late contamination",
        id="late",
        url="https://video.example/late",
    )
    window._on_search_progress(generation, SearchProgress(1, 2, late))
    assert window.review_table.item(0, 2).text() == "Title A"


def test_new_search_resets_guards_and_rejects_previous_generation(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.15)
    window.input_edit.setPlainText("First")
    window.prepare_and_search()
    old_generation = window._active_generation
    wait_idle(qtbot, window)

    window.input_edit.setPlainText("Second")
    window.prepare_and_search()
    assert window._active_generation != old_generation
    assert not window._search_terminal
    assert window.total_progress.value() == 0
    old_result = SearchResult(
        query="First",
        status=SearchStatus.FOUND,
        title="Old late result",
        id="old",
        url="https://video.example/old",
    )
    window._on_search_progress(old_generation, SearchProgress(1, 1, old_result))
    assert window.review_table.item(0, 1).text() == "Second"
    wait_idle(qtbot, window)
    assert window.review_table.item(0, 2).text() == "Título de Second"


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92
        if value <= 0.04045
        else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_visual_tokens_and_field_associations_are_accessible(qtbot) -> None:
    window, _search, _download = make_window(qtbot)

    assert _contrast(BLUE, PAPER) >= 4.5
    assert _contrast(WARNING, CREAM) >= 4.5
    assert window.input_label.buddy() is window.input_edit
    assert window.spotify_label.buddy() is window.spotify_edit
    assert window.destination_label.buddy() is window.destination_edit
    assert "&" in window.input_label.text()
    assert "&" in window.spotify_label.text()
    assert "&" in window.destination_label.text()
    for widget in (
        window.input_edit,
        window.spotify_edit,
        window.destination_edit,
        window.review_table,
        window.log_edit,
        window.total_progress,
    ):
        assert widget.accessibleName()
        assert widget.accessibleDescription()


def test_search_worker_error_uses_feminine_grammar(qtbot) -> None:
    window, _search, _download = make_window(qtbot)
    generation = window._next_generation()
    window._search_terminal = False

    window._on_worker_failed("RuntimeError: boom", generation, "search")

    assert "Pesquisa interrompida por erro inesperado" in window.summary_label.text()


def test_download_cancel_updates_summary_and_controls(qtbot, tmp_path: Path) -> None:
    window, _search, _download = make_window(qtbot, download_delay=0.3)
    window.input_edit.setPlainText("Slow Download")
    window.prepare_and_search()
    wait_idle(qtbot, window)
    window.destination_edit.setText(str(tmp_path))

    window.start_download()
    assert window.is_busy
    window.cancel_active_operation()
    wait_idle(qtbot, window)

    assert window.last_download_batch is not None
    assert window.last_download_batch.cancelled
    assert "1 cancelado" in window.summary_label.text()
    assert window.search_button.isEnabled()
    assert not window.cancel_button.isEnabled()


def test_close_during_worker_waits_for_safe_cancellation(qtbot) -> None:
    window, _search, _download = make_window(qtbot, search_delay=0.3)
    window.input_edit.setPlainText("Slow Close")
    window.prepare_and_search()
    assert window.is_busy

    window.close()
    assert window.is_busy
    qtbot.waitUntil(lambda: window._active_thread is None, timeout=3000)
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=1000)


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
