"""Main PySide6 window for the progressive prepare/review/download flow."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum
from pathlib import Path
import shutil
from typing import Any

from PySide6.QtCore import QEasingCurve, QModelIndex, QPropertyAnimation, QThread, QTimer, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import QFileDialog, QGraphicsOpacityEffect, QMainWindow, QMenu

from music_downloader.csv_importer import import_exportify_csv
from music_downloader.diagnostics import exception_diagnostic
from music_downloader.download_profiles import DEFAULT_DOWNLOAD_PROFILE, DownloadProfile, MediaKind
from music_downloader.download_service import DownloadService
from music_downloader.list_parser import parse_semicolon_list
from music_downloader.models import (
    CsvImportResult,
    DownloadBatchResult,
    DownloadProgress,
    DownloadProgressStatus,
    DownloadStatus,
    QueryListResult,
    SearchBatchResult,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from music_downloader.search_service import SearchService
from music_downloader.spotify import is_spotify_playlist_url
from music_downloader.ui.pages import (
    AddPage,
    AppShell,
    CompletionPage,
    DownloadPage,
    ImportPopover,
    OptionsPopover,
    ReviewPage,
    SearchPage,
)
from music_downloader.ui.review_model import ReviewItemDelegate, ReviewListModel, format_duration
from music_downloader.ui.styles import APP_STYLESHEET
from music_downloader.workers import DownloadWorker, SearchWorker

CsvImporter = Callable[[str | Path], CsvImportResult]
ExecutableResolver = Callable[[str], str | None]


class FlowStage(str, Enum):
    ADD = "add"
    SEARCHING = "searching"
    REVIEW = "review"
    DOWNLOADING = "downloading"
    COMPLETE = "complete"


_DOWNLOAD_STATUS_TEXT = {
    DownloadProgressStatus.DOWNLOADING: "Baixando…",
    DownloadProgressStatus.PROCESSING: "Convertendo…",
    DownloadProgressStatus.RETRYING: "Tentando novamente…",
    DownloadProgressStatus.COMPLETED: "Concluído",
    DownloadProgressStatus.ERROR: "Falha",
    DownloadProgressStatus.CANCELLED: "Cancelado",
}


class MainWindow(QMainWindow):
    """Native Windows shell with injectable services for deterministic tests."""

    def __init__(
        self,
        *,
        search_service: Any | None = None,
        download_service: Any | None = None,
        csv_importer: CsvImporter = import_exportify_csv,
        executable_resolver: ExecutableResolver = shutil.which,
    ) -> None:
        super().__init__()
        self.search_service = search_service or SearchService()
        self.download_service = download_service or DownloadService()
        self.csv_importer = csv_importer
        self.executable_resolver = executable_resolver

        self.last_parse_result: QueryListResult | None = None
        self.last_search_batch: SearchBatchResult | None = None
        self.last_download_batch: DownloadBatchResult | None = None
        self.last_notice = ""

        self._active_thread: QThread | None = None
        self._active_worker: SearchWorker | DownloadWorker | None = None
        self._operation: str | None = None
        self._busy = False
        self._close_pending = False
        self._generation_counter = 0
        self._active_generation: int | None = None

        self._search_target_row: int | None = None
        self._search_queries: tuple[str, ...] = ()
        self._search_received: dict[int, SearchResult] = {}
        self._search_terminal = True
        self._search_max_processed = 0
        self._search_found_count = 0
        self._research_previous_result: SearchResult | None = None

        self._download_rows: list[int] = []
        self._download_items: list[SearchResult] = []
        self._download_terminal = True
        self._download_terminal_items: set[int] = set()
        self._download_max_total_value = 0
        self._download_max_processed = 0
        self._download_profile = DEFAULT_DOWNLOAD_PROFILE

        self._stage = FlowStage.ADD
        self._stage_before_operation = FlowStage.ADD
        self._page_animation: QPropertyAnimation | None = None

        self.setWindowTitle("Music Downloader")
        self.resize(1060, 760)
        self.setMinimumSize(720, 600)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()
        self._connect_signals()
        self._configure_accessibility()
        self._transition_to(FlowStage.ADD)
        self.statusBar().hide()

    @property
    def is_busy(self) -> bool:
        return self._busy

    @property
    def stage(self) -> FlowStage:
        return self._stage

    @property
    def search_results(self) -> list[SearchResult]:
        return self.review_model.results

    def _build_ui(self) -> None:
        self.shell = AppShell(self)
        self.add_page = AddPage()
        self.search_page = SearchPage()
        self.review_page = ReviewPage()
        self.download_page = DownloadPage()
        self.completion_page = CompletionPage()

        self._pages = {
            FlowStage.ADD: self.add_page,
            FlowStage.SEARCHING: self.search_page,
            FlowStage.REVIEW: self.review_page,
            FlowStage.DOWNLOADING: self.download_page,
            FlowStage.COMPLETE: self.completion_page,
        }
        for page in self._pages.values():
            self.shell.stack.addWidget(page)

        self.review_model = ReviewListModel(self)
        self.review_delegate = ReviewItemDelegate(self.review_page.list_view)
        self.review_page.list_view.setModel(self.review_model)
        self.review_page.list_view.setItemDelegate(self.review_delegate)

        self.import_popover = ImportPopover(self)
        self.options_popover = OptionsPopover(self)
        self.setCentralWidget(self.shell)

        # Stable aliases used by integrations and existing tests.
        self.input_edit = self.add_page.input_edit
        self.destination_edit = self.add_page.destination_edit
        self.browse_button = self.add_page.browse_button
        self.import_csv_button = self.add_page.import_button
        self.spotify_edit = self.import_popover.spotify_edit
        self.spotify_hint_label = self.import_popover.spotify_hint_label
        self.media_kind_combo = self.options_popover.media_kind_combo
        self.audio_format_combo = self.options_popover.audio_format_combo
        self.audio_quality_combo = self.options_popover.audio_quality_combo
        self.video_format_combo = self.options_popover.video_format_combo
        self.video_resolution_combo = self.options_popover.video_resolution_combo
        self.cover_checkbox = self.options_popover.cover_checkbox
        self.cookie_browser_combo = self.options_popover.cookie_browser_combo
        self.search_button = self.add_page.search_button
        self.cancel_button = self.search_page.cancel_button
        self.review_list = self.review_page.list_view
        self.select_found_button = self.review_page.select_found_button
        self.clear_selection_button = self.review_page.clear_selection_button
        self.research_button = self.review_page.research_button
        self.download_button = self.review_page.download_button
        self.review_cancel_button = self.download_page.cancel_button
        self.total_progress = self.download_page.progress_bar
        self.log_edit = self.download_page.log_edit
        self.summary_label = self.completion_page.summary_label

    def _connect_signals(self) -> None:
        self.add_page.import_button.clicked.connect(self._show_import_popover)
        self.add_page.options_button.clicked.connect(self._show_options_from_add)
        self.add_page.browse_button.clicked.connect(self.choose_destination)
        self.add_page.search_button.clicked.connect(self.prepare_and_search)
        self.add_page.destination_edit.textChanged.connect(self._destination_changed)

        self.import_popover.csvRequested.connect(self.choose_csv)
        self.import_popover.spotify_edit.textChanged.connect(self.process_spotify_text)

        self.options_popover.profileChanged.connect(self._on_profile_changed)

        self.search_page.cancel_button.clicked.connect(self.cancel_active_operation)

        self.review_page.back_button.clicked.connect(lambda: self._transition_to(FlowStage.ADD))
        self.review_page.options_button.clicked.connect(self._show_options_from_review)
        self.review_page.change_destination_button.clicked.connect(self.choose_destination)
        self.review_page.select_found_button.clicked.connect(self.select_all_found)
        self.review_page.clear_selection_button.clicked.connect(self.clear_selection)
        self.review_page.more_button.clicked.connect(self._show_current_row_menu)
        self.review_page.download_button.clicked.connect(self.start_download)
        self.review_page.editor_cancel_button.clicked.connect(self.review_page.editor.hide)
        self.review_page.research_button.clicked.connect(self.research_from_editor)
        self.review_page.list_view.doubleClicked.connect(self._open_editor)
        self.review_page.list_view.customContextMenuRequested.connect(
            self._show_context_menu
        )
        self.review_page.list_view.selectionModel().currentChanged.connect(
            self._on_current_review_changed
        )
        self.review_delegate.actionsRequested.connect(self._show_delegate_menu)
        self.review_model.selectionCountChanged.connect(self._selection_changed)

        self.download_page.cancel_button.clicked.connect(self.cancel_active_operation)
        self.download_page.details_button.clicked.connect(self.download_page.toggle_details)

        self.completion_page.failures_button.clicked.connect(
            self.completion_page.toggle_failures
        )
        self.completion_page.open_folder_button.clicked.connect(self.open_destination_folder)
        self.completion_page.new_operation_button.clicked.connect(self.start_new_operation)

    def _configure_accessibility(self) -> None:
        self.input_edit.setAccessibleName("Músicas e links")
        self.input_edit.setAccessibleDescription(
            "Digite músicas e links de vídeos ou playlists do YouTube separados por ponto e vírgula."
        )
        self.destination_edit.setAccessibleName("Pasta de destino")
        self.destination_edit.setAccessibleDescription(
            "Pasta na qual os arquivos autorizados serão salvos."
        )
        self.spotify_edit.setAccessibleName("Playlist do Spotify")
        self.spotify_edit.setAccessibleDescription(
            "Valida a URL e orienta a exportação pelo Exportify."
        )
        self.cookie_browser_combo.setAccessibleName("Sessão do YouTube")
        self.cookie_browser_combo.setAccessibleDescription(
            "Navegador local usado pelo yt-dlp para carregar cookies."
        )
        self.review_list.setAccessibleName("Lista de revisão das músicas")
        self.review_list.setAccessibleDescription(
            "Permite selecionar resultados e abrir ações para editar ou pesquisar novamente."
        )
        self.total_progress.setAccessibleName("Progresso total dos downloads")
        self.log_edit.setAccessibleName("Detalhes técnicos do download")
        self.setTabOrder(self.input_edit, self.destination_edit)
        self.setTabOrder(self.destination_edit, self.add_page.browse_button)
        self.setTabOrder(self.add_page.browse_button, self.add_page.import_button)
        self.setTabOrder(self.add_page.import_button, self.add_page.options_button)
        self.setTabOrder(self.add_page.options_button, self.add_page.search_button)

    def _transition_to(self, stage: FlowStage) -> None:
        changed = stage is not self._stage or self.shell.stack.currentWidget() is not self._pages[stage]
        self._stage = stage
        page = self._pages[stage]
        self.shell.stack.setCurrentWidget(page)
        if changed and self.isVisible():
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(150)
            animation.setStartValue(0.86)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.finished.connect(lambda target=page: target.setGraphicsEffect(None))
            self._page_animation = animation
            animation.start()
        if stage is FlowStage.REVIEW:
            self._refresh_review_page()
        if stage is FlowStage.ADD:
            self.add_page.input_edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def _show_import_popover(self) -> None:
        self.options_popover.hide()
        self.import_popover.show_for(self.add_page.import_button)

    def _show_options_from_add(self) -> None:
        self.import_popover.hide()
        self.options_popover.show_for(self.add_page.options_button)

    def _show_options_from_review(self) -> None:
        self.import_popover.hide()
        self.options_popover.show_for(self.review_page.options_button)

    def _destination_changed(self, value: str) -> None:
        self.review_page.set_destination(value.strip())
        self._update_download_button()

    def _notice(self, message: str, *, error: bool = False) -> None:
        self.last_notice = message
        prefix = "ERRO: " if error else ""
        self.log_edit.appendPlainText(f"{prefix}{message}")
        self.statusBar().showMessage(message)
        if self._stage is FlowStage.ADD:
            self.add_page.notice.show_message(message, error=error)
        elif self._stage is FlowStage.SEARCHING and error:
            self.search_page.notice.show_message(message, error=True)
        elif self._stage is FlowStage.REVIEW:
            self.review_page.notice.show_message(message, error=error)
        elif self._stage is FlowStage.DOWNLOADING and error:
            self.download_page.error_label.show_message(message, error=True)

    def choose_csv(self) -> None:
        self.import_popover.hide()
        filename, _filter = QFileDialog.getOpenFileName(
            self,
            "Importar playlist CSV",
            "",
            "Arquivos CSV (*.csv);;Todos os arquivos (*)",
        )
        if filename:
            self.import_csv_path(Path(filename))

    def import_csv_path(self, path: str | Path) -> CsvImportResult | None:
        try:
            result = self.csv_importer(path)
        except Exception as error:
            self._notice(
                f"Não foi possível importar o CSV: {exception_diagnostic(error)}",
                error=True,
            )
            return None

        existing = parse_semicolon_list(self.input_edit.toPlainText()).queries
        imported_queries = tuple(
            " ".join(query.replace(";", ",").split()) for query in result.queries
        )
        merged = parse_semicolon_list(";".join((*existing, *imported_queries)))
        added_count = len(merged.queries) - len(existing)
        already_present = result.imported_count - added_count
        self.input_edit.setPlainText("; ".join(merged.queries))
        message = (
            f"CSV: {result.imported_count} importadas, {result.invalid_count} inválidas, "
            f"{result.duplicate_count} duplicadas no arquivo; {added_count} adicionadas"
        )
        if already_present:
            message += f", {already_present} já estavam na lista"
        self._notice(message + ".")
        return result

    def process_spotify_text(self, text: str | None = None) -> bool:
        value = self.spotify_edit.text() if text is None else text
        if not value.strip():
            self.spotify_hint_label.setText(
                "Cole um link para confirmar o fluxo Exportify e depois importe o CSV."
            )
            return False
        if is_spotify_playlist_url(value):
            self.spotify_hint_label.setText(
                "Playlist detectada. Exporte-a pelo Exportify e use “Importar arquivo CSV…”."
            )
            return True
        self.spotify_hint_label.setText(
            "O texto não é uma URL pública de playlist do Spotify."
        )
        return False

    def choose_destination(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Escolher pasta de destino",
            self.destination_edit.text().strip(),
        )
        if selected:
            self.destination_edit.setText(selected)

    def prepare_and_search(self) -> None:
        if self._busy:
            return
        parsed = parse_semicolon_list(self.input_edit.toPlainText())
        self.last_parse_result = parsed
        if not parsed.queries:
            self._notice(
                "Nenhuma música válida. Digite uma lista separada por ‘;’ ou importe um CSV.",
                error=True,
            )
            return
        self.add_page.notice.clear()
        self.input_edit.setPlainText("; ".join(parsed.queries))
        self._start_search(parsed.queries, target_row=None)

    def _start_search(self, queries: Iterable[str], target_row: int | None) -> None:
        if self._busy:
            return
        query_tuple = tuple(queries)
        generation = self._next_generation()
        self._stage_before_operation = self._stage
        self._search_queries = query_tuple
        self._search_received = {}
        self._search_terminal = False
        self._search_max_processed = 0
        self._search_found_count = 0
        self._research_previous_result = None
        if target_row is None:
            self.review_model.reset_waiting(query_tuple)
        elif 0 <= target_row < self.review_model.rowCount():
            item = self.review_model.item_at(target_row)
            self._research_previous_result = item.result if item else None
            self.review_model.set_status(target_row, "Pesquisando novamente")
        self._search_target_row = target_row
        self.search_page.reset()
        self._transition_to(FlowStage.SEARCHING)
        worker = SearchWorker(self.search_service, query_tuple, generation=generation)
        worker.progress.connect(self._on_search_progress)
        self._launch_worker(
            worker,
            self._on_search_completed,
            self._on_search_worker_failed,
            operation="search",
            generation=generation,
        )

    def _on_search_progress(self, generation: int, progress: SearchProgress) -> None:
        if not self._accept_event(generation) or self._search_terminal:
            return
        result_index = progress.processed_items - 1
        if not (
            0 <= result_index < len(self._search_queries)
            and self._search_queries[result_index] == progress.result.query
        ):
            try:
                result_index = self._search_queries.index(progress.result.query)
            except ValueError:
                if not 0 <= result_index < len(self._search_queries):
                    return
        self._search_received[result_index] = progress.result
        row = result_index if self._search_target_row is None else self._search_target_row
        self.review_model.set_result(row, progress.result)
        self._search_max_processed = max(
            self._search_max_processed,
            min(len(self._search_queries), max(0, progress.processed_items)),
        )
        if progress.result.status is SearchStatus.FOUND:
            self._search_found_count += 1
            self.search_page.set_found_count(self._search_found_count)

    def _on_search_completed(self, generation: int, batch: SearchBatchResult) -> None:
        if not self._accept_event(generation) or self._search_terminal:
            return
        self._search_terminal = True
        self.last_search_batch = batch
        displayed_results: list[SearchResult] = []
        if self._search_target_row is None:
            result_queries = [result.query for result in batch.results]
            input_queries = set(self._search_queries)
            has_expansion = (
                len(batch.results) != len(self._search_queries)
                or len(set(result_queries)) != len(result_queries)
                or any(query not in input_queries for query in result_queries)
            )
            if has_expansion:
                displayed_results.extend(batch.results)
            else:
                batch_by_query = {result.query: result for result in batch.results}
                for index, query in enumerate(self._search_queries):
                    result = self._search_received.get(index) or batch_by_query.get(query)
                    if result is not None:
                        displayed_results.append(result)
            self.review_model.reset_results(displayed_results)
        else:
            result = self._search_received.get(0)
            if result is None and batch.results:
                result = batch.results[0]
            if result is not None:
                displayed_results.append(result)
                self.review_model.set_result(self._search_target_row, result)
            elif self._research_previous_result is not None:
                self.review_model.set_result(
                    self._search_target_row, self._research_previous_result
                )

        all_results = self.search_results
        found = sum(result.status is SearchStatus.FOUND for result in all_results)
        missing = sum(result.status is SearchStatus.NO_RESULT for result in all_results)
        errors = sum(result.status is SearchStatus.ERROR for result in all_results)
        cancelled = " Pesquisa cancelada." if batch.cancelled else ""
        message = (
            f"Pesquisa concluída: {found} encontrados, {missing} sem resultado, "
            f"{errors} erros.{cancelled}"
        )
        if self.review_model.rowCount() or self._search_target_row is not None:
            self._transition_to(FlowStage.REVIEW)
            if missing or errors or batch.cancelled:
                self.review_page.notice.show_message(message, error=bool(errors))
            else:
                self.review_page.notice.clear()
        else:
            self._transition_to(FlowStage.ADD)
            self.add_page.notice.show_message(message, error=not batch.cancelled)
        self.last_notice = message
        self.statusBar().showMessage(message)

    def _refresh_review_page(self) -> None:
        found = sum(
            result.status is SearchStatus.FOUND for result in self.search_results
        )
        review = len(self.search_results) - found
        self.review_page.update_summary(found, review)
        self.review_page.set_destination(self.destination_edit.text().strip())
        has_rows = self.review_model.rowCount() > 0
        self.review_page.select_found_button.setVisible(has_rows)
        self.review_page.clear_selection_button.setVisible(has_rows)
        self.review_page.more_button.setVisible(has_rows)
        self._update_download_button()

    def _on_current_review_changed(
        self, current: QModelIndex, _previous: QModelIndex
    ) -> None:
        self.review_page.more_button.setEnabled(current.isValid() and not self._busy)

    def _selection_changed(self, _count: int) -> None:
        self._update_download_button()

    def select_all_found(self) -> None:
        self.review_model.select_all_found()

    def clear_selection(self) -> None:
        self.review_model.clear_selection()

    def _selected_results(self) -> tuple[list[SearchResult], list[int]]:
        return self.review_model.selected_results()

    def _on_profile_changed(self, _profile: DownloadProfile | None) -> None:
        self._update_download_button()

    def current_download_profile(self) -> DownloadProfile:
        return self.options_popover.get_profile()

    def _update_download_button(self) -> None:
        try:
            profile = self.current_download_profile()
        except (TypeError, ValueError):
            message = "Configuração de formato inválida"
            self.review_page.download_button.setText(message)
            self.review_page.download_button.setToolTip(
                "Abra Opções e selecione um tipo, formato e qualidade válidos."
            )
            self.review_page.download_button.setAccessibleName(message)
            self.review_page.download_button.setEnabled(False)
            return
        self.review_page.update_download_cta(
            self.review_model.selected_count,
            has_destination=bool(self.destination_edit.text().strip()) and not self._busy,
            profile=profile,
        )

    def _open_editor(self, index: QModelIndex) -> None:
        if self._busy or not index.isValid():
            return
        self.review_page.list_view.setCurrentIndex(index)
        item = self.review_model.item_at(index.row())
        if item is None:
            return
        self.review_page.query_edit.setText(item.result.query)
        self.review_page.editor.show()
        self.review_page.query_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.review_page.query_edit.selectAll()

    def research_from_editor(self) -> None:
        row = self.review_page.list_view.currentIndex().row()
        query = self.review_page.query_edit.text().strip()
        if row < 0:
            self._notice("Selecione uma música para pesquisar novamente.", error=True)
            return
        if not query:
            self._notice("A consulta da música está vazia.", error=True)
            return
        self.review_model.edit_query(row, query)
        self.review_page.editor.hide()
        self._start_search((query,), target_row=row)

    def research_current_row(self) -> None:
        index = self.review_page.list_view.currentIndex()
        item = self.review_model.item_at(index.row()) if index.isValid() else None
        if item is None:
            self._notice("Selecione uma música para pesquisar novamente.", error=True)
            return
        self._start_search((item.result.query,), target_row=index.row())

    def _show_delegate_menu(self, index: QModelIndex) -> None:
        self.review_page.list_view.setCurrentIndex(index)
        rect = self.review_page.list_view.visualRect(index)
        position = self.review_page.list_view.viewport().mapToGlobal(rect.bottomRight())
        self._show_row_menu(index, position)

    def _show_context_menu(self, position) -> None:
        index = self.review_page.list_view.indexAt(position)
        if not index.isValid():
            return
        self.review_page.list_view.setCurrentIndex(index)
        self._show_row_menu(
            index, self.review_page.list_view.viewport().mapToGlobal(position)
        )

    def _show_current_row_menu(self) -> None:
        index = self.review_page.list_view.currentIndex()
        if not index.isValid():
            return
        position = self.review_page.more_button.mapToGlobal(
            self.review_page.more_button.rect().bottomLeft()
        )
        self._show_row_menu(index, position)

    def _show_row_menu(self, index: QModelIndex, position) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction("Editar busca…")
        research_action = menu.addAction("Pesquisar novamente")
        chosen = menu.exec(position)
        if chosen is edit_action:
            self._open_editor(index)
        elif chosen is research_action:
            self.review_page.list_view.setCurrentIndex(index)
            self.research_current_row()

    def start_download(self) -> None:
        if self._busy:
            return
        destination = self.destination_edit.text().strip()
        if not destination:
            self._transition_to(FlowStage.REVIEW)
            self._notice("Escolha uma pasta de destino antes de baixar.", error=True)
            return
        selected, rows = self._selected_results()
        if not selected:
            self._transition_to(FlowStage.REVIEW)
            self._notice("Marque pelo menos um resultado encontrado para baixar.", error=True)
            return

        try:
            profile = self.current_download_profile()
        except (TypeError, ValueError) as error:
            self._transition_to(FlowStage.REVIEW)
            self._notice(
                f"Configuração de formato inválida: {exception_diagnostic(error)}",
                error=True,
            )
            return

        generation = self._next_generation()
        self._stage_before_operation = self._stage
        self._download_rows = rows
        self._download_items = selected
        self._download_terminal = False
        self._download_terminal_items = set()
        self._download_max_total_value = 0
        self._download_max_processed = 0
        self._download_profile = profile
        for row in rows:
            self.review_model.set_status(row, "Pronto", "Aguardando")
        self.download_page.reset(len(selected))
        self._transition_to(FlowStage.DOWNLOADING)

        worker = DownloadWorker(
            self.download_service,
            selected,
            destination,
            profile=profile,
            embed_thumbnail=self.cover_checkbox.isChecked() and profile.supports_thumbnail,
            aria2c_path=self.executable_resolver("aria2c"),
            cookie_browser=self.cookie_browser_combo.currentData(),
            generation=generation,
        )
        worker.progress.connect(self._on_download_progress)
        self._launch_worker(
            worker,
            self._on_download_completed,
            self._on_download_worker_failed,
            operation="download",
            generation=generation,
        )

    def _on_download_progress(
        self, generation: int, progress: DownloadProgress
    ) -> None:
        if not self._accept_event(generation) or self._download_terminal:
            return
        index = progress.item_index - 1
        if (
            not 0 <= index < len(self._download_rows)
            or progress.item_index in self._download_terminal_items
        ):
            return
        row = self._download_rows[index]
        status_text = _DOWNLOAD_STATUS_TEXT[progress.status]
        progress_text = (
            status_text
            if progress.item_fraction is None
            else f"{int(progress.item_fraction * 100)}%"
        )
        self.review_model.set_status(row, status_text.rstrip("…"), progress_text)
        current = self._download_items[index]
        self.download_page.current_title.setText(current.title or current.query)
        self.download_page.status_label.setText(status_text)

        terminal = progress.status in {
            DownloadProgressStatus.COMPLETED,
            DownloadProgressStatus.ERROR,
            DownloadProgressStatus.CANCELLED,
        }
        completed_units = float(progress.processed_items)
        if not terminal:
            completed_units += progress.item_fraction or 0.0
        candidate_value = min(
            100, int(completed_units / max(1, progress.total_items) * 100)
        )
        self._download_max_total_value = max(
            self._download_max_total_value,
            self.download_page.progress_bar.value(),
            candidate_value,
        )
        self.download_page.progress_bar.setValue(self._download_max_total_value)
        self._download_max_processed = max(
            self._download_max_processed, progress.processed_items
        )
        self.download_page.count_label.setText(
            f"{self._download_max_processed} de {progress.total_items} concluídos"
        )
        if terminal:
            self._download_terminal_items.add(progress.item_index)

    def _on_download_completed(
        self, generation: int, batch: DownloadBatchResult
    ) -> None:
        if not self._accept_event(generation) or self._download_terminal:
            return
        self._download_terminal = True
        self.last_download_batch = batch
        if batch.preflight_error:
            self._transition_to(FlowStage.REVIEW)
            self._notice(f"Download não iniciado: {batch.preflight_error}", error=True)
            return

        failure_details: list[str] = []
        for index, outcome in enumerate(batch.results):
            if index >= len(self._download_rows):
                break
            row = self._download_rows[index]
            status = {
                DownloadStatus.COMPLETED: "Concluído",
                DownloadStatus.ERROR: "Falha",
                DownloadStatus.CANCELLED: "Cancelado",
            }[outcome.status]
            self.review_model.set_status(
                row,
                status,
                "100%" if outcome.status is DownloadStatus.COMPLETED else status,
            )
            model_index = self.review_model.index(row)
            self.review_model.setData(
                model_index, Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole
            )
            if outcome.status is DownloadStatus.ERROR:
                detail = f"{outcome.query}: {outcome.error or 'sem diagnóstico'}"
                failure_details.append(detail)
                self.log_edit.appendPlainText(f"Falha em “{detail}”")

        unprocessed = max(0, len(self._download_rows) - len(batch.results))
        cancelled_count = sum(
            result.status is DownloadStatus.CANCELLED for result in batch.results
        ) + (unprocessed if batch.cancelled else 0)

        media_kind = self._download_profile.media_kind
        if batch.cancelled:
            for row in self._download_rows[len(batch.results) :]:
                self.review_model.set_status(row, "Cancelado", "Cancelado")
            if unprocessed:
                noun = "áudio" if media_kind is MediaKind.AUDIO else "vídeo"
                if unprocessed != 1:
                    noun += "s"
                verb = "foi processado" if unprocessed == 1 else "foram processados"
                failure_details.append(
                    f"{unprocessed} {noun} não {verb} devido ao cancelamento."
                )

        destination = self.destination_edit.text().strip()
        self._download_max_total_value = 100
        self.download_page.progress_bar.setValue(100)
        self.completion_page.show_result(
            successful=batch.successful_count,
            failed=batch.failed_count,
            cancelled=cancelled_count,
            destination=destination,
            failure_details=failure_details,
            media_kind=media_kind,
        )
        message = (
            f"Resumo: {batch.successful_count} sucesso(s), {batch.failed_count} falha(s), "
            f"{cancelled_count} cancelado(s). Pasta: {destination}"
        )
        self.last_notice = message
        self.statusBar().showMessage(message)
        self._transition_to(FlowStage.COMPLETE)

    def open_destination_folder(self) -> bool:
        destination = self.destination_edit.text().strip()
        if not destination or not Path(destination).exists():
            self._notice("A pasta de destino não está disponível.", error=True)
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(destination))))

    def start_new_operation(self) -> None:
        # Preserve current fields exactly as the legacy single-window UI did.
        self.completion_page.failures_edit.hide()
        self._transition_to(FlowStage.ADD)

    def _next_generation(self) -> int:
        self._generation_counter += 1
        self._active_generation = self._generation_counter
        return self._generation_counter

    def _accept_event(self, generation: int | None) -> bool:
        return generation is None or generation == self._active_generation

    def _launch_worker(
        self,
        worker: SearchWorker | DownloadWorker,
        completed_handler: Callable[[int, Any], None],
        failed_handler: Callable[[int, str], None],
        *,
        operation: str,
        generation: int,
    ) -> None:
        if self._active_thread is not None:
            raise RuntimeError("uma operação já está em execução")
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(completed_handler)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        worker.failed.connect(failed_handler)
        worker.failed.connect(thread.quit)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._active_thread = thread
        self._active_worker = worker
        self._operation = operation
        self._active_generation = generation
        self._set_busy(True)
        thread.start()

    def _on_search_worker_failed(self, generation: int, diagnostic: str) -> None:
        self._on_worker_failed(diagnostic, generation, "search")

    def _on_download_worker_failed(self, generation: int, diagnostic: str) -> None:
        self._on_worker_failed(diagnostic, generation, "download")

    def _on_worker_failed(
        self,
        diagnostic: str,
        generation: int | None = None,
        operation: str | None = None,
    ) -> None:
        if not self._accept_event(generation):
            return
        operation_name = operation or self._operation
        if operation_name == "search":
            self._search_terminal = True
            message = f"Pesquisa interrompida por erro inesperado: {diagnostic}"
            target = (
                FlowStage.REVIEW
                if self._search_target_row is not None or self.review_model.rowCount()
                else FlowStage.ADD
            )
        else:
            self._download_terminal = True
            message = f"Download interrompido por erro inesperado: {diagnostic}"
            target = FlowStage.REVIEW
        self._transition_to(target)
        self._notice(message, error=True)

    def _on_thread_finished(self) -> None:
        self._active_worker = None
        self._active_thread = None
        self._operation = None
        self._set_busy(False)
        if self._close_pending:
            self._close_pending = False
            QTimer.singleShot(0, self.close)

    def cancel_active_operation(self) -> None:
        if self._active_worker is None:
            return
        self._active_worker.cancel()
        self.search_page.cancel_button.setEnabled(False)
        self.download_page.cancel_button.setEnabled(False)
        self.log_edit.appendPlainText("Cancelamento solicitado pelo usuário.")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.options_popover.set_busy(busy)
        for widget in (
            self.input_edit,
            self.destination_edit,
            self.add_page.browse_button,
            self.add_page.import_button,
            self.add_page.options_button,
            self.add_page.search_button,
            self.review_page.back_button,
            self.review_page.options_button,
            self.review_page.change_destination_button,
            self.review_page.select_found_button,
            self.review_page.clear_selection_button,
            self.review_page.more_button,
            self.review_page.list_view,
            self.review_page.query_edit,
            self.review_page.research_button,
            self.review_page.editor_cancel_button,
            self.completion_page.open_folder_button,
            self.completion_page.new_operation_button,
        ):
            widget.setEnabled(not busy)
        self.search_page.cancel_button.setEnabled(busy and self._operation == "search")
        self.download_page.cancel_button.setEnabled(
            busy and self._operation == "download"
        )
        self.import_popover.setEnabled(not busy)
        self._update_download_button()

    @staticmethod
    def _format_duration(duration: float | None) -> str:
        return format_duration(duration)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._active_thread is not None and self._active_thread.isRunning():
            self._close_pending = True
            self.cancel_active_operation()
            event.ignore()
            return
        event.accept()
