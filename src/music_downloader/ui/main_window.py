"""Main PySide6 window for the complete prepare/review/download flow."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path
import shutil
from typing import Any

from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from music_downloader.csv_importer import import_exportify_csv
from music_downloader.diagnostics import exception_diagnostic
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
from music_downloader.ui.styles import APP_STYLESHEET
from music_downloader.workers import DownloadWorker, SearchWorker

CsvImporter = Callable[[str | Path], CsvImportResult]
ExecutableResolver = Callable[[str], str | None]

_SEARCH_STATUS_TEXT = {
    SearchStatus.FOUND: "Encontrado",
    SearchStatus.NO_RESULT: "Sem resultado",
    SearchStatus.ERROR: "Erro",
}

_DOWNLOAD_STATUS_TEXT = {
    DownloadProgressStatus.DOWNLOADING: "Baixando",
    DownloadProgressStatus.PROCESSING: "Convertendo",
    DownloadProgressStatus.RETRYING: "Nova tentativa",
    DownloadProgressStatus.COMPLETED: "Concluído",
    DownloadProgressStatus.ERROR: "Falha",
    DownloadProgressStatus.CANCELLED: "Cancelado",
}


class MainWindow(QMainWindow):
    """Single-window desktop flow with injectable services for offline tests."""

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

        self.search_results: list[SearchResult] = []
        self.last_parse_result: QueryListResult | None = None
        self.last_search_batch: SearchBatchResult | None = None
        self.last_download_batch: DownloadBatchResult | None = None
        self.last_notice = ""

        self._active_thread: QThread | None = None
        self._active_worker: SearchWorker | DownloadWorker | None = None
        self._operation: str | None = None
        self._generation_counter = 0
        self._active_generation: int | None = None
        self._search_target_row: int | None = None
        self._search_queries: tuple[str, ...] = ()
        self._search_received: dict[int, SearchResult] = {}
        self._search_terminal = True
        self._search_max_processed = 0
        self._research_previous_result: SearchResult | None = None
        self._download_rows: list[int] = []
        self._download_terminal = True
        self._download_terminal_items: set[int] = set()
        self._download_max_total_value = 0
        self._updating_table = False
        self._busy = False
        self._close_pending = False

        self.setWindowTitle("Music Downloader — preparação autorizada")
        self.resize(1180, 780)
        self.setMinimumSize(900, 640)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()
        self._connect_signals()
        self._configure_accessibility()
        self.statusBar().showMessage("Pronto para preparar uma lista autorizada.")

    @property
    def is_busy(self) -> bool:
        return self._busy

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)

        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 8, 14, 8)
        title = QLabel("MUSIC DOWNLOADER // DESKTOP")
        title.setObjectName("appTitle")
        subtitle = QLabel(
            "Prepare, revise e baixe apenas músicas que você possui ou pode baixar."
        )
        subtitle.setObjectName("appSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_input_panel())
        splitter.addWidget(self._build_review_panel())
        splitter.addWidget(self._build_activity_panel())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([230, 330, 180])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)

    def _build_input_panel(self) -> QWidget:
        group = QGroupBox("01 // ENTRADA")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 18, 10, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText(
            "Ex.: Save a Prayer Duran Duran; The Winner Takes It All ABBA"
        )
        self.input_edit.setMaximumBlockCount(10000)
        self.input_label = QLabel("&Lista separada por ponto e vírgula (;):")
        self.input_label.setBuddy(self.input_edit)
        layout.addWidget(self.input_label, 0, 0, 1, 4)
        layout.addWidget(self.input_edit, 1, 0, 1, 4)

        self.import_csv_button = QPushButton("Importar CSV…")
        layout.addWidget(self.import_csv_button, 2, 0)
        self.spotify_edit = QLineEdit()
        self.spotify_edit.setPlaceholderText("https://open.spotify.com/playlist/…")
        self.spotify_label = QLabel("&Playlist Spotify:")
        self.spotify_label.setBuddy(self.spotify_edit)
        layout.addWidget(self.spotify_label, 2, 1)
        layout.addWidget(self.spotify_edit, 2, 2, 1, 2)

        self.spotify_hint_label = QLabel(
            "Links são detectados; no MVP, exporte pelo Exportify e importe o CSV."
        )
        self.spotify_hint_label.setObjectName("spotifyHint")
        self.spotify_hint_label.setWordWrap(True)
        layout.addWidget(self.spotify_hint_label, 3, 0, 1, 4)

        self.destination_edit = QLineEdit()
        self.destination_edit.setPlaceholderText("Escolha onde salvar os MP3")
        self.destination_label = QLabel("&Destino:")
        self.destination_label.setBuddy(self.destination_edit)
        layout.addWidget(self.destination_label, 4, 0)
        layout.addWidget(self.destination_edit, 4, 1, 1, 2)
        self.browse_button = QPushButton("Escolher…")
        layout.addWidget(self.browse_button, 4, 3)

        self.cover_checkbox = QCheckBox("Incorporar thumbnail como capa")
        layout.addWidget(self.cover_checkbox, 5, 0, 1, 2)
        self.search_button = QPushButton("Pesquisar músicas")
        self.search_button.setObjectName("primaryButton")
        layout.addWidget(self.search_button, 5, 2)
        self.cancel_button = QPushButton("Cancelar operação")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button, 5, 3)
        layout.setColumnStretch(2, 1)
        return group

    def _build_review_panel(self) -> QWidget:
        group = QGroupBox("02 // REVISÃO")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 18, 8, 8)
        self.review_table = QTableWidget(0, 7)
        self.review_table.setHorizontalHeaderLabels(
            [
                "Baixar",
                "Consulta",
                "Título encontrado",
                "Canal",
                "Duração",
                "Status",
                "Progresso",
            ]
        )
        self.review_table.setAlternatingRowColors(True)
        self.review_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.review_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.review_table.verticalHeader().setVisible(False)
        header = self.review_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for column in (3, 4, 5, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.review_table, 1)

        actions = QHBoxLayout()
        self.select_found_button = QPushButton("Marcar encontrados")
        self.clear_selection_button = QPushButton("Desmarcar todos")
        self.research_button = QPushButton("Pesquisar linha selecionada")
        self.download_button = QPushButton("Baixar selecionadas")
        self.download_button.setObjectName("primaryButton")
        self.download_button.setEnabled(False)
        actions.addWidget(self.select_found_button)
        actions.addWidget(self.clear_selection_button)
        actions.addWidget(self.research_button)
        actions.addStretch(1)
        actions.addWidget(self.download_button)
        layout.addLayout(actions)
        return group

    def _build_activity_panel(self) -> QWidget:
        group = QGroupBox("03 // ATIVIDADE")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 18, 8, 8)
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        layout.addWidget(self.total_progress)
        self.summary_label = QLabel("Nenhuma operação executada nesta sessão.")
        self.summary_label.setObjectName("summaryLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(500)
        self.log_edit.setPlaceholderText("Eventos e falhas resumidas aparecem aqui.")
        layout.addWidget(self.log_edit, 1)
        return group

    def _connect_signals(self) -> None:
        self.import_csv_button.clicked.connect(self.choose_csv)
        self.spotify_edit.textChanged.connect(self.process_spotify_text)
        self.browse_button.clicked.connect(self.choose_destination)
        self.search_button.clicked.connect(self.prepare_and_search)
        self.cancel_button.clicked.connect(self.cancel_active_operation)
        self.select_found_button.clicked.connect(self.select_all_found)
        self.clear_selection_button.clicked.connect(self.clear_selection)
        self.research_button.clicked.connect(self.research_current_row)
        self.download_button.clicked.connect(self.start_download)
        self.review_table.itemChanged.connect(self._on_table_item_changed)
        self.review_table.itemSelectionChanged.connect(self._update_action_buttons)

    def _configure_accessibility(self) -> None:
        self.input_edit.setAccessibleName("Lista de músicas")
        self.input_edit.setAccessibleDescription(
            "Digite consultas separadas por ponto e vírgula ou importe um CSV."
        )
        self.spotify_edit.setAccessibleName("Link público da playlist Spotify")
        self.spotify_edit.setAccessibleDescription(
            "Detecta playlists e orienta a exportação pelo Exportify."
        )
        self.destination_edit.setAccessibleName("Pasta de destino")
        self.destination_edit.setAccessibleDescription(
            "Pasta na qual os arquivos MP3 autorizados serão salvos."
        )
        self.review_table.setAccessibleName("Tabela de revisão das músicas")
        self.review_table.setAccessibleDescription(
            "Permite editar consultas, selecionar resultados e acompanhar estados."
        )
        self.log_edit.setAccessibleName("Log da operação")
        self.log_edit.setAccessibleDescription(
            "Resumo textual de eventos, cancelamentos e falhas."
        )
        self.total_progress.setAccessibleName("Progresso total")
        self.total_progress.setAccessibleDescription(
            "Percentual concluído da pesquisa ou do lote de downloads."
        )
        self.setTabOrder(self.input_edit, self.import_csv_button)
        self.setTabOrder(self.import_csv_button, self.spotify_edit)
        self.setTabOrder(self.spotify_edit, self.destination_edit)
        self.setTabOrder(self.destination_edit, self.browse_button)
        self.setTabOrder(self.browse_button, self.cover_checkbox)
        self.setTabOrder(self.cover_checkbox, self.search_button)

    def _notice(self, message: str, *, error: bool = False) -> None:
        self.last_notice = message
        prefix = "ERRO: " if error else ""
        self.log_edit.appendPlainText(f"{prefix}{message}")
        self.statusBar().showMessage(message)

    def choose_csv(self) -> None:
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
        # Exportify may separate multiple artists with semicolons inside one
        # CSV cell. The free-text editor uses the same character between songs,
        # so represent those internal separators as commas before merging.
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
        message += "."
        self._notice(message)
        return result

    def process_spotify_text(self, text: str | None = None) -> bool:
        value = self.spotify_edit.text() if text is None else text
        if not value.strip():
            self.spotify_hint_label.setText(
                "Links são detectados; no MVP, exporte pelo Exportify e importe o CSV."
            )
            return False
        if is_spotify_playlist_url(value):
            self.spotify_hint_label.setText(
                "Playlist Spotify detectada. Exporte-a no Exportify e use “Importar CSV…”. "
                "Uma lista digitada acima continua válida."
            )
            return True
        self.spotify_hint_label.setText(
            "O texto não é uma URL pública de playlist do Spotify. Você ainda pode "
            "pesquisar a lista digitada acima."
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
        self.process_spotify_text()
        parsed = parse_semicolon_list(self.input_edit.toPlainText())
        self.last_parse_result = parsed
        if not parsed.queries:
            self._notice(
                "Nenhuma música válida. Digite uma lista separada por ‘;’ ou importe um CSV.",
                error=True,
            )
            return

        self.input_edit.setPlainText("; ".join(parsed.queries))
        self._notice(
            f"Lista preparada: {len(parsed.queries)} consultas, "
            f"{parsed.duplicate_count} duplicadas e {parsed.empty_count} vazias ignoradas."
        )
        self._start_search(parsed.queries, target_row=None)

    def research_current_row(self) -> None:
        if self._busy:
            return
        row = self.review_table.currentRow()
        if row < 0 or row >= len(self.search_results):
            self._notice("Selecione uma linha da revisão para pesquisar novamente.", error=True)
            return
        item = self.review_table.item(row, 1)
        query = item.text().strip() if item else ""
        if not query:
            self._notice("A consulta da linha selecionada está vazia.", error=True)
            return
        self._start_search((query,), target_row=row)

    def _start_search(self, queries: Iterable[str], target_row: int | None) -> None:
        if self._busy:
            return
        query_tuple = tuple(queries)
        generation = self._next_generation()
        self._search_queries = query_tuple
        self._search_received = {}
        self._search_terminal = False
        self._search_max_processed = 0
        self._research_previous_result = None
        if target_row is None:
            self._updating_table = True
            try:
                self.review_table.setRowCount(0)
                self.search_results.clear()
            finally:
                self._updating_table = False
            for row, query in enumerate(query_tuple):
                self._set_result_at_row(
                    row, SearchResult(query=query, status=SearchStatus.NO_RESULT)
                )
                status_item = self.review_table.item(row, 5)
                if status_item:
                    status_item.setText("Aguardando pesquisa")
        elif 0 <= target_row < len(self.search_results):
            self._research_previous_result = self.search_results[target_row]
            status_item = self.review_table.item(target_row, 5)
            if status_item:
                status_item.setText("Pesquisando novamente")
        self._search_target_row = target_row
        self.total_progress.setValue(0)
        self.summary_label.setText("Pesquisando metadados sem iniciar downloads…")
        worker = SearchWorker(
            self.search_service, query_tuple, generation=generation
        )
        worker.progress.connect(self._on_search_progress)
        self._launch_worker(
            worker,
            self._on_search_completed,
            self._on_search_worker_failed,
            operation="search",
            generation=generation,
        )

    def _on_search_progress(
        self, generation: int, progress: SearchProgress
    ) -> None:
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
        row = (
            result_index
            if self._search_target_row is None
            else self._search_target_row
        )
        self._set_result_at_row(row, progress.result)
        self._search_max_processed = max(
            self._search_max_processed,
            min(len(self._search_queries), max(0, progress.processed_items)),
        )
        percent = int(
            self._search_max_processed * 100 / max(1, len(self._search_queries))
        )
        self.total_progress.setValue(max(self.total_progress.value(), percent))
        self.statusBar().showMessage(
            f"Pesquisa: {self._search_max_processed}/{len(self._search_queries)} concluídas."
        )

    def _on_search_completed(
        self, generation: int, batch: SearchBatchResult
    ) -> None:
        if not self._accept_event(generation) or self._search_terminal:
            return
        self._search_terminal = True
        self.last_search_batch = batch
        batch_by_query = {result.query: result for result in batch.results}
        displayed_results: list[SearchResult] = []
        if self._search_target_row is None:
            for index, query in enumerate(self._search_queries):
                result = self._search_received.get(index) or batch_by_query.get(query)
                if result is not None:
                    displayed_results.append(result)
            self._updating_table = True
            try:
                self.review_table.setRowCount(0)
                self.search_results.clear()
            finally:
                self._updating_table = False
            for row, result in enumerate(displayed_results):
                self._set_result_at_row(row, result)
        else:
            result = self._search_received.get(0)
            if result is None and batch.results:
                result = batch.results[0]
            if result is not None:
                displayed_results.append(result)
                self._set_result_at_row(self._search_target_row, result)
            elif self._research_previous_result is not None:
                self._set_result_at_row(
                    self._search_target_row, self._research_previous_result
                )

        found = sum(result.status is SearchStatus.FOUND for result in displayed_results)
        missing = sum(
            result.status is SearchStatus.NO_RESULT for result in displayed_results
        )
        errors = sum(result.status is SearchStatus.ERROR for result in displayed_results)
        cancelled = " Operação cancelada." if batch.cancelled else ""
        message = (
            f"Pesquisa concluída: {found} encontrados, {missing} sem resultado, "
            f"{errors} erros.{cancelled}"
        )
        self.summary_label.setText(message)
        self._notice(message)

    def _set_result_at_row(self, row: int, result: SearchResult) -> None:
        self._updating_table = True
        try:
            if row >= self.review_table.rowCount():
                self.review_table.insertRow(row)
                self.search_results.append(result)
            else:
                self.search_results[row] = result

            select_item = QTableWidgetItem()
            select_flags = (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            if result.status is not SearchStatus.FOUND:
                select_flags &= ~Qt.ItemFlag.ItemIsUserCheckable
            select_item.setFlags(select_flags)
            select_item.setCheckState(
                Qt.CheckState.Checked
                if result.status is SearchStatus.FOUND
                else Qt.CheckState.Unchecked
            )
            self.review_table.setItem(row, 0, select_item)

            query_item = QTableWidgetItem(result.query)
            query_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )
            self.review_table.setItem(row, 1, query_item)
            self._set_readonly_cell(row, 2, result.title or "—")
            self._set_readonly_cell(row, 3, result.channel or "—")
            self._set_readonly_cell(row, 4, self._format_duration(result.duration))
            status_item = self._set_readonly_cell(
                row, 5, _SEARCH_STATUS_TEXT[result.status]
            )
            if result.error:
                status_item.setToolTip(result.error)
                self.log_edit.appendPlainText(f"Falha em “{result.query}”: {result.error}")
            self._set_readonly_cell(row, 6, "—")
        finally:
            self._updating_table = False
        self._update_action_buttons()

    def _set_readonly_cell(self, row: int, column: int, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.review_table.setItem(row, column, item)
        return item

    @staticmethod
    def _format_duration(duration: float | None) -> str:
        if duration is None:
            return "—"
        seconds = max(0, int(duration))
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02d}"

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table:
            return
        row = item.row()
        if item.column() == 1 and row < len(self.search_results):
            query = item.text().strip()
            current = self.search_results[row]
            if query != current.query:
                self._updating_table = True
                try:
                    self.search_results[row] = SearchResult(
                        query=query,
                        status=SearchStatus.NO_RESULT,
                    )
                    select_item = self.review_table.item(row, 0)
                    if select_item:
                        select_item.setCheckState(Qt.CheckState.Unchecked)
                        select_item.setFlags(
                            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                        )
                    for column in (2, 3, 4):
                        cell = self.review_table.item(row, column)
                        if cell:
                            cell.setText("—")
                    status = self.review_table.item(row, 5)
                    if status:
                        status.setText("Editado — pesquise novamente")
                    progress = self.review_table.item(row, 6)
                    if progress:
                        progress.setText("—")
                finally:
                    self._updating_table = False
        self._update_action_buttons()

    def select_all_found(self) -> None:
        self._updating_table = True
        try:
            for row, result in enumerate(self.search_results):
                item = self.review_table.item(row, 0)
                if item and result.status is SearchStatus.FOUND:
                    item.setCheckState(Qt.CheckState.Checked)
        finally:
            self._updating_table = False
        self._update_action_buttons()

    def clear_selection(self) -> None:
        self._updating_table = True
        try:
            for row in range(self.review_table.rowCount()):
                item = self.review_table.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Unchecked)
        finally:
            self._updating_table = False
        self._update_action_buttons()

    def _selected_results(self) -> tuple[list[SearchResult], list[int]]:
        selected: list[SearchResult] = []
        rows: list[int] = []
        for row, result in enumerate(self.search_results):
            select_item = self.review_table.item(row, 0)
            if (
                result.status is SearchStatus.FOUND
                and select_item
                and select_item.checkState() is Qt.CheckState.Checked
            ):
                query_item = self.review_table.item(row, 1)
                query = query_item.text().strip() if query_item else result.query
                selected.append(replace(result, query=query))
                rows.append(row)
        return selected, rows

    def start_download(self) -> None:
        if self._busy:
            return
        destination = self.destination_edit.text().strip()
        if not destination:
            self._notice("Escolha uma pasta de destino antes de baixar.", error=True)
            return
        selected, rows = self._selected_results()
        if not selected:
            self._notice("Marque pelo menos um resultado encontrado para baixar.", error=True)
            return

        generation = self._next_generation()
        self._download_rows = rows
        self._download_terminal = False
        self._download_terminal_items = set()
        self._download_max_total_value = 0
        self.total_progress.setValue(0)
        self.summary_label.setText(f"Preparando {len(selected)} downloads aprovados…")
        self._updating_table = True
        try:
            for row in rows:
                progress = self.review_table.item(row, 6)
                if progress:
                    progress.setText("Aguardando")
        finally:
            self._updating_table = False

        worker = DownloadWorker(
            self.download_service,
            selected,
            destination,
            embed_thumbnail=self.cover_checkbox.isChecked(),
            aria2c_path=self.executable_resolver("aria2c"),
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
        status_item = self.review_table.item(row, 5)
        if status_item:
            status_item.setText(status_text)
        progress_item = self.review_table.item(row, 6)
        if progress_item:
            if progress.item_fraction is None:
                progress_item.setText(status_text)
            else:
                progress_item.setText(f"{int(progress.item_fraction * 100)}%")
        terminal = progress.status in {
            DownloadProgressStatus.COMPLETED,
            DownloadProgressStatus.ERROR,
            DownloadProgressStatus.CANCELLED,
        }
        completed_units = float(progress.processed_items)
        if not terminal:
            completed_units += progress.item_fraction or 0.0
        total_fraction = completed_units / max(1, progress.total_items)
        candidate_value = min(100, int(total_fraction * 100))
        self._download_max_total_value = max(
            self._download_max_total_value,
            self.total_progress.value(),
            candidate_value,
        )
        self.total_progress.setValue(self._download_max_total_value)
        if terminal:
            self._download_terminal_items.add(progress.item_index)
        self.statusBar().showMessage(
            f"Downloads: item {progress.item_index}/{progress.total_items} — {status_text}."
        )

    def _on_download_completed(
        self, generation: int, batch: DownloadBatchResult
    ) -> None:
        if not self._accept_event(generation) or self._download_terminal:
            return
        self._download_terminal = True
        self.last_download_batch = batch
        if batch.preflight_error:
            message = f"Download não iniciado: {batch.preflight_error}"
            self.summary_label.setText(message)
            self._notice(message, error=True)
            return

        for index, outcome in enumerate(batch.results):
            if index >= len(self._download_rows):
                break
            row = self._download_rows[index]
            status = {
                DownloadStatus.COMPLETED: "Concluído",
                DownloadStatus.ERROR: "Falha",
                DownloadStatus.CANCELLED: "Cancelado",
            }[outcome.status]
            status_item = self.review_table.item(row, 5)
            progress_item = self.review_table.item(row, 6)
            if status_item:
                status_item.setText(status)
                if outcome.error:
                    status_item.setToolTip(outcome.error)
            if progress_item:
                progress_item.setText("100%" if outcome.status is DownloadStatus.COMPLETED else status)
            select_item = self.review_table.item(row, 0)
            if select_item:
                select_item.setCheckState(Qt.CheckState.Unchecked)
            if outcome.status is DownloadStatus.ERROR:
                self.log_edit.appendPlainText(
                    f"Falha em “{outcome.query}”: {outcome.error or 'sem diagnóstico'}"
                )

        unprocessed = max(0, len(self._download_rows) - len(batch.results))
        cancelled_count = sum(
            result.status is DownloadStatus.CANCELLED for result in batch.results
        ) + (unprocessed if batch.cancelled else 0)
        if batch.cancelled:
            for row in self._download_rows[len(batch.results) :]:
                status_item = self.review_table.item(row, 5)
                progress_item = self.review_table.item(row, 6)
                if status_item:
                    status_item.setText("Cancelado")
                if progress_item:
                    progress_item.setText("Cancelado")

        destination = self.destination_edit.text().strip()
        message = (
            f"Resumo: {batch.successful_count} sucesso(s), {batch.failed_count} falha(s), "
            f"{cancelled_count} cancelado(s). Pasta: {destination}"
        )
        self._download_max_total_value = 100
        self.total_progress.setValue(100)
        self.summary_label.setText(message)
        self._notice(message)

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
        else:
            self._download_terminal = True
            message = f"Download interrompido por erro inesperado: {diagnostic}"
        self.summary_label.setText(message)
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
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage("Cancelamento solicitado; aguardando ponto seguro…")
        self.log_edit.appendPlainText("Cancelamento solicitado pelo usuário.")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.input_edit.setEnabled(not busy)
        self.spotify_edit.setEnabled(not busy)
        self.destination_edit.setEnabled(not busy)
        self.cover_checkbox.setEnabled(not busy)
        self.import_csv_button.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.search_button.setEnabled(not busy)
        self.research_button.setEnabled(not busy and self.review_table.currentRow() >= 0)
        self.select_found_button.setEnabled(not busy and bool(self.search_results))
        self.clear_selection_button.setEnabled(not busy and bool(self.search_results))
        self.cancel_button.setEnabled(busy)
        self.review_table.setEnabled(not busy)
        self._update_download_button()

    def _update_action_buttons(self) -> None:
        self.research_button.setEnabled(
            not self._busy and self.review_table.currentRow() >= 0
        )
        has_rows = bool(self.search_results)
        self.select_found_button.setEnabled(not self._busy and has_rows)
        self.clear_selection_button.setEnabled(not self._busy and has_rows)
        self._update_download_button()

    def _update_download_button(self) -> None:
        selected, _rows = self._selected_results()
        self.download_button.setEnabled(not self._busy and bool(selected))

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._active_thread is not None and self._active_thread.isRunning():
            self._close_pending = True
            self.cancel_active_operation()
            event.ignore()
            return
        event.accept()
