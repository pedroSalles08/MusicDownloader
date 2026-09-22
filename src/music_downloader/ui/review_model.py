"""Presentation model and delegate for the music review list."""

from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import QAbstractListModel, QEvent, QModelIndex, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from music_downloader.models import SearchResult, SearchStatus
from music_downloader.ui.styles import (
    ACCENT,
    CUE,
    ERROR,
    SEPARATOR,
    SURFACE,
    SUCCESS,
    SURFACE_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
)


def format_duration(duration: float | None) -> str:
    if duration is None:
        return "—"
    minutes, seconds = divmod(max(0, int(duration)), 60)
    return f"{minutes}:{seconds:02d}"


_SEARCH_STATUS_TEXT = {
    SearchStatus.FOUND: "Encontrado",
    SearchStatus.NO_RESULT: "Sem resultado",
    SearchStatus.ERROR: "Erro",
}


@dataclass(slots=True)
class ReviewItemState:
    """UI-only state layered over one immutable domain result."""

    result: SearchResult
    selected: bool
    status_text: str
    progress_text: str = ""

    @classmethod
    def from_result(cls, result: SearchResult) -> "ReviewItemState":
        return cls(
            result=result,
            selected=result.status is SearchStatus.FOUND,
            status_text=_SEARCH_STATUS_TEXT[result.status],
        )


class ReviewListModel(QAbstractListModel):
    """Single source of truth for review selection and presentation state."""

    ResultRole = Qt.ItemDataRole.UserRole + 1
    QueryRole = Qt.ItemDataRole.UserRole + 2
    ChannelRole = Qt.ItemDataRole.UserRole + 3
    DurationRole = Qt.ItemDataRole.UserRole + 4
    StatusRole = Qt.ItemDataRole.UserRole + 5
    ProgressRole = Qt.ItemDataRole.UserRole + 6

    selectionCountChanged = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[ReviewItemState] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802 - Qt API
        roles = super().roleNames()
        roles.update(
            {
                int(self.ResultRole): b"result",
                int(self.QueryRole): b"query",
                int(self.ChannelRole): b"channel",
                int(self.DurationRole): b"duration",
                int(self.StatusRole): b"status",
                int(self.ProgressRole): b"progress",
            }
        )
        return roles

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        result = item.result
        if role == Qt.ItemDataRole.DisplayRole:
            return result.title or result.query
        if role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if item.selected else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.ToolTipRole:
            details = [result.title or result.query, result.query]
            if result.channel:
                details.append(result.channel)
            if result.error:
                details.append(result.error)
            return "\n".join(dict.fromkeys(details))
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return self._accessible_text(item)
        if role == self.ResultRole:
            return result
        if role == self.QueryRole:
            return result.query
        if role == self.ChannelRole:
            return result.channel or ""
        if role == self.DurationRole:
            return format_duration(result.duration)
        if role == self.StatusRole:
            return item.status_text
        if role == self.ProgressRole:
            return item.progress_text
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self._items[index.row()].result.status is SearchStatus.FOUND:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return False
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.CheckStateRole:
            if item.result.status is not SearchStatus.FOUND:
                return False
            selected = (
                value == Qt.CheckState.Checked
                or value == Qt.CheckState.Checked.value
            )
            if selected == item.selected:
                return False
            item.selected = selected
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            self.selectionCountChanged.emit(self.selected_count)
            return True
        return False

    @property
    def results(self) -> list[SearchResult]:
        return [item.result for item in self._items]

    @property
    def selected_count(self) -> int:
        return sum(item.selected for item in self._items)

    def item_at(self, row: int) -> ReviewItemState | None:
        return self._items[row] if 0 <= row < len(self._items) else None

    def reset_results(self, results) -> None:
        self.beginResetModel()
        self._items = [ReviewItemState.from_result(result) for result in results]
        self.endResetModel()
        self.selectionCountChanged.emit(self.selected_count)

    def reset_waiting(self, queries) -> None:
        self.beginResetModel()
        self._items = [
            ReviewItemState(
                SearchResult(query=query, status=SearchStatus.NO_RESULT),
                selected=False,
                status_text="Aguardando pesquisa",
            )
            for query in queries
        ]
        self.endResetModel()
        self.selectionCountChanged.emit(0)

    def set_result(self, row: int, result: SearchResult) -> None:
        if not 0 <= row < len(self._items):
            return
        self._items[row] = ReviewItemState.from_result(result)
        index = self.index(row)
        self.dataChanged.emit(index, index)
        self.selectionCountChanged.emit(self.selected_count)

    def set_status(self, row: int, status: str, progress: str = "") -> None:
        if not 0 <= row < len(self._items):
            return
        item = self._items[row]
        item.status_text = status
        item.progress_text = progress
        index = self.index(row)
        self.dataChanged.emit(index, index, [self.StatusRole, self.ProgressRole])

    def edit_query(self, row: int, query: str) -> bool:
        if not 0 <= row < len(self._items):
            return False
        normalized = query.strip()
        current = self._items[row]
        if not normalized or normalized == current.result.query:
            return bool(normalized)
        current.result = SearchResult(query=normalized, status=SearchStatus.NO_RESULT)
        current.selected = False
        current.status_text = "Editado — pesquise novamente"
        current.progress_text = ""
        index = self.index(row)
        self.dataChanged.emit(index, index)
        self.selectionCountChanged.emit(self.selected_count)
        return True

    def select_all_found(self) -> None:
        changed = False
        for item in self._items:
            selected = item.result.status is SearchStatus.FOUND
            changed = changed or item.selected != selected
            item.selected = selected
        if changed and self._items:
            self.dataChanged.emit(
                self.index(0),
                self.index(len(self._items) - 1),
                [Qt.ItemDataRole.CheckStateRole],
            )
        self.selectionCountChanged.emit(self.selected_count)

    def clear_selection(self) -> None:
        changed = any(item.selected for item in self._items)
        for item in self._items:
            item.selected = False
        if changed and self._items:
            self.dataChanged.emit(
                self.index(0),
                self.index(len(self._items) - 1),
                [Qt.ItemDataRole.CheckStateRole],
            )
        self.selectionCountChanged.emit(0)

    def selected_results(self) -> tuple[list[SearchResult], list[int]]:
        results: list[SearchResult] = []
        rows: list[int] = []
        for row, item in enumerate(self._items):
            if item.selected and item.result.status is SearchStatus.FOUND:
                results.append(replace(item.result, query=item.result.query))
                rows.append(row)
        return results, rows

    @staticmethod
    def _accessible_text(item: ReviewItemState) -> str:
        result = item.result
        selection = "selecionada" if item.selected else "não selecionada"
        parts = [result.title or result.query, result.channel or result.query]
        if result.duration is not None:
            parts.append(format_duration(result.duration))
        parts.extend((item.status_text, selection))
        return ", ".join(part for part in parts if part)


class ReviewItemDelegate(QStyledItemDelegate):
    """Paint a compact review row in the app's midnight-deck visual language."""

    actionsRequested = Signal(object)

    ROW_HEIGHT = 64

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._music_icon = QIcon(":/icons/music.svg")
        self._check_icon = QIcon(":/icons/check.svg")

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802
        return QSize(1, self.ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected:
            painter.fillRect(rect.adjusted(1, 0, -1, 0), QColor("#22324A"))
        elif hovered:
            painter.fillRect(rect.adjusted(1, 0, -1, 0), QColor(SURFACE_HOVER))

        check_rect = self._check_rect(rect)
        checkable = bool(index.flags() & Qt.ItemFlag.ItemIsUserCheckable)
        checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(ACCENT if checkable else SEPARATOR), 1))
        painter.setBrush(QColor(ACCENT if checked else SURFACE))
        painter.drawRoundedRect(check_rect, 4, 4)
        if checked:
            self._check_icon.paint(painter, check_rect.adjusted(1, 1, -1, -1))

        icon_rect = QRect(check_rect.right() + 14, rect.center().y() - 11, 22, 22)
        self._music_icon.paint(painter, icon_rect)

        right_margin = 18
        actions_rect = self._actions_rect(rect)
        status = str(index.data(ReviewListModel.StatusRole) or "")
        progress = str(index.data(ReviewListModel.ProgressRole) or "")
        status_display = status
        if progress and progress.casefold() != status.casefold():
            status_display = f"{status} · {progress}"
        duration = str(index.data(ReviewListModel.DurationRole) or "")
        status_width = min(
            170, max(88, painter.fontMetrics().horizontalAdvance(status_display) + 18)
        )
        duration_width = 48
        status_left = actions_rect.left() - 12 - status_width
        duration_left = status_left - duration_width - 12
        text_left = icon_rect.right() + 14
        text_right = max(text_left + 80, duration_left - 14)

        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        title_font = QFont(option.font)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(TEXT_PRIMARY))
        title_rect = QRect(text_left, rect.top() + 11, text_right - text_left, 21)
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, title_rect.width()),
        )

        query = str(index.data(ReviewListModel.QueryRole) or "")
        channel = str(index.data(ReviewListModel.ChannelRole) or "")
        metadata = "  ·  ".join(part for part in (query, channel) if part)
        meta_font = QFont(option.font)
        meta_font.setPointSizeF(max(8.5, option.font.pointSizeF() - 0.5))
        painter.setFont(meta_font)
        painter.setPen(QColor(TEXT_SECONDARY))
        meta_rect = QRect(text_left, rect.top() + 34, text_right - text_left, 18)
        painter.drawText(
            meta_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(metadata, Qt.TextElideMode.ElideRight, meta_rect.width()),
        )

        painter.setPen(QColor(TEXT_TERTIARY))
        painter.drawText(
            QRect(duration_left, rect.top(), duration_width, rect.height()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            duration,
        )
        status_color = TEXT_SECONDARY
        status_background = QColor("#1B2430")
        status_border = QColor("#465364")
        lowered = status.casefold()
        if "erro" in lowered or "falha" in lowered:
            status_color = ERROR
            status_background = QColor("#321B1E")
            status_border = QColor("#714043")
        elif any(
            marker in lowered
            for marker in ("sem resultado", "editado", "tentativa", "tentando", "cancelado")
        ):
            status_color = CUE
            status_background = QColor("#302516")
            status_border = QColor("#6D5531")
        elif "encontrado" in lowered or "concluído" in lowered or "pronto" in lowered:
            status_color = SUCCESS
            status_background = QColor("#162A22")
            status_border = QColor("#35654A")
        elif any(
            marker in lowered
            for marker in ("pesquis", "aguardando", "baixando", "convertendo")
        ):
            status_color = ACCENT
            status_background = QColor("#192941")
            status_border = QColor("#3D5E8B")
        status_rect = QRect(
            status_left,
            rect.center().y() - 12,
            status_width,
            24,
        )
        painter.setPen(QPen(status_border, 1))
        painter.setBrush(status_background)
        painter.drawRoundedRect(QRectF(status_rect), 6, 6)
        painter.setPen(QColor(status_color))
        painter.drawText(
            status_rect.adjusted(8, 0, -8, 0),
            Qt.AlignmentFlag.AlignCenter,
            painter.fontMetrics().elidedText(
                status_display, Qt.TextElideMode.ElideRight, status_width - 16
            ),
        )
        painter.setPen(QPen(QColor("#465364"), 1))
        painter.setBrush(QColor("#202A35" if selected or hovered else SURFACE))
        painter.drawRoundedRect(QRectF(actions_rect), 6, 6)
        painter.setPen(QColor(TEXT_SECONDARY if selected or hovered else TEXT_TERTIARY))
        painter.drawText(actions_rect, Qt.AlignmentFlag.AlignCenter, "⋯")

        painter.setPen(QPen(QColor(SEPARATOR), 1))
        painter.drawLine(rect.left() + 44, rect.bottom(), rect.right() - right_margin, rect.bottom())
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:  # noqa: N802
        if isinstance(event, QMouseEvent) and event.type() == QEvent.Type.MouseButtonRelease:
            if (
                event.button() == Qt.MouseButton.LeftButton
                and self._check_rect(option.rect).contains(event.position().toPoint())
            ):
                if index.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
                    model.setData(
                        index,
                        Qt.CheckState.Unchecked if checked else Qt.CheckState.Checked,
                        Qt.ItemDataRole.CheckStateRole,
                    )
                    return True
            if self._actions_rect(option.rect).contains(event.position().toPoint()):
                self.actionsRequested.emit(index)
                return True
        return super().editorEvent(event, model, option, index)

    @staticmethod
    def _check_rect(rect: QRect) -> QRect:
        return QRect(rect.left() + 14, rect.center().y() - 9, 18, 18)

    @staticmethod
    def _actions_rect(rect: QRect) -> QRect:
        return QRect(rect.right() - 38, rect.top() + 14, 30, rect.height() - 28)
