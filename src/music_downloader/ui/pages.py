"""Progressive pages and reusable UI components for the main window."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from music_downloader.browser_cookies import (
    COOKIE_BROWSER_LABELS,
    detect_default_cookie_browser,
)
from music_downloader.download_profiles import (
    AUDIO_BITRATE_CHOICES,
    DEFAULT_DOWNLOAD_PROFILE,
    VIDEO_HEIGHT_CHOICES,
    AudioFormat,
    DownloadProfile,
    MediaKind,
    VideoFormat,
)
from music_downloader.ui import resources_rc as _resources_rc  # noqa: F401
from music_downloader.ui.styles import (
    ACCENT,
    CUE,
    SEPARATOR,
    SURFACE_HOVER,
    TEXT_TERTIARY,
)


def _set_button_icon(button: QPushButton | QToolButton, name: str) -> None:
    """Apply one consistently sized local outline icon to a text button."""

    button.setIcon(QIcon(f":/icons/{name}.svg"))
    button.setIconSize(QSize(16, 16))


class FlowRail(QWidget):
    """A compact playhead-like indicator for the five real workflow stages."""

    STAGE_COUNT = 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._stage = 0
        self.setFixedSize(164, 16)
        self.setAccessibleName("Progresso do fluxo")

    def set_stage(self, stage: int, label: str) -> None:
        self._stage = min(max(0, stage), self.STAGE_COUNT - 1)
        self.setAccessibleDescription(
            f"Etapa {self._stage + 1} de {self.STAGE_COUNT}: {label}."
        )
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        left = 7.0
        right = float(self.width() - 7)
        middle = self.height() / 2
        interval = (right - left) / (self.STAGE_COUNT - 1)
        points = [left + interval * index for index in range(self.STAGE_COUNT)]

        painter.setPen(QPen(QColor(SEPARATOR), 2.0))
        painter.drawLine(round(left), round(middle), round(right), round(middle))
        painter.setPen(QPen(QColor(ACCENT), 2.0))
        painter.drawLine(
            round(left), round(middle), round(points[self._stage]), round(middle)
        )

        for index, x in enumerate(points):
            if index < self._stage:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(ACCENT))
                radius = 3.5
            elif index == self._stage:
                painter.setPen(QPen(QColor(CUE), 2.0))
                painter.setBrush(QColor("#0E131A"))
                radius = 5.0
            else:
                painter.setPen(QPen(QColor(TEXT_TERTIARY), 1.2))
                painter.setBrush(QColor(SURFACE_HOVER))
                radius = 3.0
            painter.drawEllipse(
                QRectF(x - radius, middle - radius, radius * 2, radius * 2)
            )


class ElidedPathLabel(QLabel):
    """Keep long Windows paths inside compact action areas without losing the tooltip."""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(parent)
        self._full_text = text
        self.setMinimumWidth(0)
        self._refresh_text()

    def set_path(self, value: str) -> None:
        self._full_text = value
        self.setToolTip(value)
        self.setAccessibleName(
            f"Pasta de destino: {value}" if value else "Pasta de destino não definida"
        )
        self._refresh_text()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._refresh_text()

    def _refresh_text(self) -> None:
        visible = self._full_text or "Destino não definido"
        width = max(40, self.contentsRect().width())
        super().setText(
            self.fontMetrics().elidedText(visible, Qt.TextElideMode.ElideMiddle, width)
        )


class NoticeBanner(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("noticeBanner")
        self.setWordWrap(True)
        self.hide()

    def show_message(self, message: str, *, error: bool = False) -> None:
        self.setText(message)
        self.setProperty("severity", "error" if error else "warning")
        self.style().unpolish(self)
        self.style().polish(self)
        self.show()

    def clear(self) -> None:
        self.setText("")
        self.hide()


class PopupFrame(QFrame):
    """Keyboard-friendly popup anchored to a normal button."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("popover")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def show_for(self, anchor: QWidget) -> None:
        self.adjustSize()
        origin = anchor.mapToGlobal(QPoint(anchor.width() - self.width(), anchor.height() + 8))
        screen = anchor.screen().availableGeometry()
        x = min(max(screen.left() + 8, origin.x()), screen.right() - self.width() - 8)
        y = min(max(screen.top() + 8, origin.y()), screen.bottom() - self.height() - 8)
        self.move(x, y)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self._fade_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_animation.setDuration(140)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.start()


class ImportPopover(PopupFrame):
    csvRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("Importar músicas")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.csv_button = QPushButton("Importar arquivo CSV…")
        self.csv_button.setObjectName("primaryButton")
        _set_button_icon(self.csv_button, "import-dark")
        self.csv_button.clicked.connect(self.csvRequested)
        layout.addWidget(self.csv_button)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #2C2C2E;")
        layout.addWidget(divider)

        spotify_title = QLabel("Playlist do Spotify")
        spotify_title.setObjectName("sectionTitle")
        layout.addWidget(spotify_title)
        self.spotify_edit = QLineEdit()
        self.spotify_edit.setPlaceholderText("https://open.spotify.com/playlist/…")
        layout.addWidget(self.spotify_edit)
        self.spotify_hint_label = QLabel(
            "Cole um link para confirmar o fluxo Exportify e depois importe o CSV."
        )
        self.spotify_hint_label.setObjectName("secondaryText")
        self.spotify_hint_label.setWordWrap(True)
        layout.addWidget(self.spotify_hint_label)


def _as_media_kind(value: Any) -> MediaKind:
    return value if isinstance(value, MediaKind) else MediaKind(str(value))


def _as_audio_format(value: Any) -> AudioFormat | None:
    if value is None:
        return None
    return value if isinstance(value, AudioFormat) else AudioFormat(str(value))


def _as_video_format(value: Any) -> VideoFormat | None:
    if value is None:
        return None
    return value if isinstance(value, VideoFormat) else VideoFormat(str(value))


_VIDEO_FORMAT_HINTS = {
    VideoFormat.MP4_COMPATIBLE: "H.264/AAC, maior compatibilidade, mais lento por recodificar.",
    VideoFormat.MP4_FAST: "Evita recodificação e depende de streams MP4/M4A disponíveis.",
    VideoFormat.WEBM: "Preserva streams WebM compatíveis.",
    VideoFormat.ORIGINAL: "Preserva a seleção/container entregue pelo yt-dlp; a extensão pode variar.",
}


class OptionsPopover(PopupFrame):
    profileChanged = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(360)
        self._busy = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("popoverContent")
        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Opções")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Tipo de mídia
        media_kind_label = QLabel("Tipo de mídia")
        media_kind_label.setObjectName("secondaryText")
        layout.addWidget(media_kind_label)

        self.media_kind_combo = QComboBox()
        self.media_kind_combo.addItem("Somente áudio", MediaKind.AUDIO)
        self.media_kind_combo.addItem("Vídeo", MediaKind.VIDEO)
        self.media_kind_combo.setAccessibleName("Tipo de mídia")
        self.media_kind_combo.setAccessibleDescription(
            "Escolha entre baixar somente áudio ou vídeo com imagem."
        )
        media_kind_label.setBuddy(self.media_kind_combo)
        layout.addWidget(self.media_kind_combo)

        # Audio section container
        self.audio_container = QWidget()
        self.audio_container.setObjectName("popoverSection")
        audio_layout = QVBoxLayout(self.audio_container)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(8)

        audio_format_label = QLabel("Formato")
        audio_format_label.setObjectName("secondaryText")
        audio_layout.addWidget(audio_format_label)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItem("MP3", AudioFormat.MP3)
        self.audio_format_combo.addItem("M4A", AudioFormat.M4A)
        self.audio_format_combo.addItem("Opus", AudioFormat.OPUS)
        self.audio_format_combo.addItem("AAC (.m4a)", AudioFormat.AAC)
        self.audio_format_combo.addItem("Vorbis (.ogg)", AudioFormat.VORBIS)
        self.audio_format_combo.addItem("FLAC", AudioFormat.FLAC)
        self.audio_format_combo.addItem("ALAC (.m4a)", AudioFormat.ALAC)
        self.audio_format_combo.addItem("WAV", AudioFormat.WAV)
        self.audio_format_combo.setAccessibleName("Formato de áudio")
        self.audio_format_combo.setAccessibleDescription("Formato do arquivo de áudio final.")
        audio_format_label.setBuddy(self.audio_format_combo)
        audio_layout.addWidget(self.audio_format_combo)

        # Lossy audio quality
        self.audio_quality_widget = QWidget()
        self.audio_quality_widget.setObjectName("popoverField")
        quality_layout = QVBoxLayout(self.audio_quality_widget)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(8)
        self.audio_quality_label = QLabel("Qualidade")
        self.audio_quality_label.setObjectName("secondaryText")
        quality_layout.addWidget(self.audio_quality_label)

        self.audio_quality_combo = QComboBox()
        for bitrate in AUDIO_BITRATE_CHOICES:
            suffix = " (padrão)" if bitrate == 192 else ""
            self.audio_quality_combo.addItem(f"{bitrate} kbps{suffix}", bitrate)
        self.audio_quality_combo.setCurrentIndex(
            self.audio_quality_combo.findData(192)
        )
        self.audio_quality_combo.setAccessibleName("Qualidade do áudio")
        self.audio_quality_combo.setAccessibleDescription(
            "Taxa de bits (bitrate) para formatos de áudio com perdas."
        )
        self.audio_quality_label.setBuddy(self.audio_quality_combo)
        quality_layout.addWidget(self.audio_quality_combo)
        audio_layout.addWidget(self.audio_quality_widget)

        # Lossless audio info
        self.audio_lossless_widget = QWidget()
        self.audio_lossless_widget.setObjectName("popoverField")
        lossless_layout = QVBoxLayout(self.audio_lossless_widget)
        lossless_layout.setContentsMargins(0, 0, 0, 0)
        lossless_layout.setSpacing(6)
        lossless_header = QHBoxLayout()
        lossless_title = QLabel("Qualidade")
        lossless_title.setObjectName("secondaryText")
        lossless_header.addWidget(lossless_title)
        lossless_badge = QLabel("Sem perdas")
        lossless_badge.setObjectName("losslessBadge")
        lossless_header.addWidget(lossless_badge)
        lossless_header.addStretch(1)
        lossless_layout.addLayout(lossless_header)

        self.audio_lossless_help_label = QLabel(
            "Converter uma fonte comprimida para um formato sem perdas não recupera qualidade."
        )
        self.audio_lossless_help_label.setObjectName("tertiaryText")
        self.audio_lossless_help_label.setWordWrap(True)
        lossless_layout.addWidget(self.audio_lossless_help_label)
        self.audio_lossless_widget.hide()
        audio_layout.addWidget(self.audio_lossless_widget)

        layout.addWidget(self.audio_container)

        # Video section container
        self.video_container = QWidget()
        self.video_container.setObjectName("popoverSection")
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(8)

        video_format_label = QLabel("Formato")
        video_format_label.setObjectName("secondaryText")
        video_layout.addWidget(video_format_label)

        self.video_format_combo = QComboBox()
        self.video_format_combo.addItem("MP4 compatível", VideoFormat.MP4_COMPATIBLE)
        self.video_format_combo.addItem("MP4 rápido", VideoFormat.MP4_FAST)
        self.video_format_combo.addItem("WebM", VideoFormat.WEBM)
        self.video_format_combo.addItem("Original", VideoFormat.ORIGINAL)
        self.video_format_combo.setAccessibleName("Formato de vídeo")
        self.video_format_combo.setAccessibleDescription(
            "Formato e perfil de compatibilidade do arquivo de vídeo."
        )
        video_format_label.setBuddy(self.video_format_combo)
        video_layout.addWidget(self.video_format_combo)

        self.video_resolution_widget = QWidget()
        self.video_resolution_widget.setObjectName("popoverField")
        resolution_layout = QVBoxLayout(self.video_resolution_widget)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(8)
        self.video_resolution_label = QLabel("Resolução máxima")
        self.video_resolution_label.setObjectName("secondaryText")
        resolution_layout.addWidget(self.video_resolution_label)

        self.video_resolution_combo = QComboBox()
        self.video_resolution_combo.addItem("Melhor disponível", None)
        for height in reversed(VIDEO_HEIGHT_CHOICES):
            self.video_resolution_combo.addItem(f"{height}p", height)
        self.video_resolution_combo.setAccessibleName("Resolução máxima do vídeo")
        self.video_resolution_combo.setAccessibleDescription(
            "Limite máximo de altura do vídeo em pixels."
        )
        self.video_resolution_label.setBuddy(self.video_resolution_combo)
        resolution_layout.addWidget(self.video_resolution_combo)
        video_layout.addWidget(self.video_resolution_widget)

        self.video_help_label = QLabel(
            _VIDEO_FORMAT_HINTS[VideoFormat.MP4_COMPATIBLE]
        )
        self.video_help_label.setObjectName("secondaryText")
        self.video_help_label.setWordWrap(True)
        video_layout.addWidget(self.video_help_label)

        self.video_container.hide()
        layout.addWidget(self.video_container)

        # Divider
        divider1 = QFrame()
        divider1.setObjectName("popoverDivider")
        divider1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider1)

        # Cover checkbox
        self.cover_checkbox = QCheckBox("Incorporar thumbnail como capa")
        self.cover_checkbox.setAccessibleName("Incorporar thumbnail como capa")
        self.cover_checkbox.setAccessibleDescription(
            "Incorpora a capa nos metadados do arquivo quando compatível."
        )
        layout.addWidget(self.cover_checkbox)

        # Divider
        divider2 = QFrame()
        divider2.setObjectName("popoverDivider")
        divider2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider2)

        # YouTube session
        session_label = QLabel("Sessão do YouTube")
        session_label.setObjectName("secondaryText")
        layout.addWidget(session_label)
        self.cookie_browser_combo = QComboBox()
        self.cookie_browser_combo.addItem("Sem cookies", None)
        for browser, label in COOKIE_BROWSER_LABELS:
            self.cookie_browser_combo.addItem(label, browser)
        default_index = self.cookie_browser_combo.findData(detect_default_cookie_browser())
        if default_index >= 0:
            self.cookie_browser_combo.setCurrentIndex(default_index)
        self.cookie_browser_combo.setAccessibleName("Sessão do YouTube")
        self.cookie_browser_combo.setAccessibleDescription(
            "Navegador local usado pelo yt-dlp para carregar cookies."
        )
        session_label.setBuddy(self.cookie_browser_combo)
        layout.addWidget(self.cookie_browser_combo)

        hint = QLabel(
            "Use o navegador em que você já está conectado. Os cookies são lidos "
            "localmente pelo yt-dlp e não são exibidos pelo aplicativo."
        )
        hint.setObjectName("secondaryText")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # Connect combo change handlers
        self.media_kind_combo.currentIndexChanged.connect(self._on_controls_changed)
        self.audio_format_combo.currentIndexChanged.connect(self._on_controls_changed)
        self.audio_quality_combo.currentIndexChanged.connect(self._on_controls_changed)
        self.video_format_combo.currentIndexChanged.connect(self._on_controls_changed)
        self.video_resolution_combo.currentIndexChanged.connect(self._on_controls_changed)
        self._on_controls_changed()

    def show_for(self, anchor: QWidget) -> None:
        self._fit_height_to_screen(anchor.screen())
        super().show_for(anchor)

    def _fit_height_to_screen(self, screen: Any) -> None:
        content_layout = self.scroll_content.layout()
        if content_layout is not None:
            content_layout.activate()
        desired_height = self.scroll_content.sizeHint().height()
        available_height = screen.availableGeometry().height()
        self.scroll_area.setFixedHeight(
            min(desired_height, max(280, available_height - 40))
        )
        self.adjustSize()

    def _on_controls_changed(self) -> None:
        try:
            media_kind = _as_media_kind(self.media_kind_combo.currentData())
        except (TypeError, ValueError):
            self.audio_container.hide()
            self.video_container.hide()
            self.cover_checkbox.setChecked(False)
            self.cover_checkbox.setEnabled(False)
            self.cover_checkbox.setToolTip(
                "Selecione um tipo de mídia válido para configurar a thumbnail."
            )
            self.profileChanged.emit(None)
            return
        is_audio = media_kind == MediaKind.AUDIO
        self.audio_container.setVisible(is_audio)
        self.video_container.setVisible(not is_audio)

        if is_audio:
            raw_audio_format = self.audio_format_combo.currentData()
            audio_format = _as_audio_format(raw_audio_format) or AudioFormat.MP3
            is_lossless = audio_format in {AudioFormat.ALAC, AudioFormat.FLAC, AudioFormat.WAV}
            self.audio_quality_widget.setVisible(not is_lossless)
            self.audio_lossless_widget.setVisible(is_lossless)
        else:
            raw_video_format = self.video_format_combo.currentData()
            video_format = _as_video_format(raw_video_format) or VideoFormat.MP4_COMPATIBLE
            self.video_help_label.setText(_VIDEO_FORMAT_HINTS.get(video_format, ""))
            is_original = video_format == VideoFormat.ORIGINAL
            self.video_resolution_widget.setVisible(not is_original)

        try:
            profile = self.get_profile()
        except (TypeError, ValueError):
            self.cover_checkbox.setChecked(False)
            self.cover_checkbox.setEnabled(False)
            self.cover_checkbox.setToolTip(
                "Selecione um formato e uma qualidade válidos."
            )
            self.profileChanged.emit(None)
            return
        if not profile.supports_thumbnail:
            self.cover_checkbox.setChecked(False)
            self.cover_checkbox.setEnabled(False)
            self.cover_checkbox.setToolTip(
                "A incorporação de thumbnail não é suportada para este formato."
            )
        else:
            self.cover_checkbox.setEnabled(not self._busy)
            self.cover_checkbox.setToolTip("")

        if self.isVisible():
            self._fit_height_to_screen(self.screen())

        self.profileChanged.emit(profile)

    def get_profile(self) -> DownloadProfile:
        raw_media_kind = self.media_kind_combo.currentData()
        media_kind = _as_media_kind(raw_media_kind)
        if media_kind == MediaKind.AUDIO:
            raw_audio_format = self.audio_format_combo.currentData()
            audio_format = _as_audio_format(raw_audio_format) or AudioFormat.MP3
            if audio_format in {AudioFormat.ALAC, AudioFormat.FLAC, AudioFormat.WAV}:
                bitrate = None
            else:
                raw_bitrate = self.audio_quality_combo.currentData()
                bitrate = 192 if raw_bitrate is None else int(raw_bitrate)
            return DownloadProfile.for_audio(audio_format, bitrate_kbps=bitrate)
        elif media_kind == MediaKind.VIDEO:
            raw_video_format = self.video_format_combo.currentData()
            video_format = _as_video_format(raw_video_format) or VideoFormat.MP4_COMPATIBLE
            if video_format == VideoFormat.ORIGINAL:
                max_height = None
            else:
                raw_height = self.video_resolution_combo.currentData()
                max_height = int(raw_height) if raw_height is not None else None
            return DownloadProfile.for_video(video_format, max_height=max_height)
        raise ValueError(f"Tipo de mídia inválido: {media_kind}")

    def set_profile(self, profile: DownloadProfile) -> None:
        self.media_kind_combo.blockSignals(True)
        self.audio_format_combo.blockSignals(True)
        self.audio_quality_combo.blockSignals(True)
        self.video_format_combo.blockSignals(True)
        self.video_resolution_combo.blockSignals(True)
        try:
            kind_idx = self.media_kind_combo.findData(profile.media_kind)
            if kind_idx < 0:
                kind_idx = self.media_kind_combo.findData(profile.media_kind.value)
            if kind_idx >= 0:
                self.media_kind_combo.setCurrentIndex(kind_idx)
            if profile.media_kind == MediaKind.AUDIO:
                if profile.audio_format is not None:
                    fmt_idx = self.audio_format_combo.findData(profile.audio_format)
                    if fmt_idx < 0:
                        fmt_idx = self.audio_format_combo.findData(profile.audio_format.value)
                    if fmt_idx >= 0:
                        self.audio_format_combo.setCurrentIndex(fmt_idx)
                if profile.audio_bitrate_kbps is not None:
                    bit_idx = self.audio_quality_combo.findData(profile.audio_bitrate_kbps)
                    if bit_idx >= 0:
                        self.audio_quality_combo.setCurrentIndex(bit_idx)
            elif profile.media_kind == MediaKind.VIDEO:
                if profile.video_format is not None:
                    fmt_idx = self.video_format_combo.findData(profile.video_format)
                    if fmt_idx < 0:
                        fmt_idx = self.video_format_combo.findData(profile.video_format.value)
                    if fmt_idx >= 0:
                        self.video_format_combo.setCurrentIndex(fmt_idx)
                res_idx = self.video_resolution_combo.findData(profile.max_video_height)
                if res_idx >= 0:
                    self.video_resolution_combo.setCurrentIndex(res_idx)
        finally:
            self.media_kind_combo.blockSignals(False)
            self.audio_format_combo.blockSignals(False)
            self.audio_quality_combo.blockSignals(False)
            self.video_format_combo.blockSignals(False)
            self.video_resolution_combo.blockSignals(False)
        self._on_controls_changed()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.media_kind_combo.setEnabled(not busy)
        self.audio_format_combo.setEnabled(not busy)
        self.audio_quality_combo.setEnabled(not busy)
        self.video_format_combo.setEnabled(not busy)
        self.video_resolution_combo.setEnabled(not busy)
        self.cookie_browser_combo.setEnabled(not busy)
        if busy:
            self.cover_checkbox.setEnabled(False)
        else:
            try:
                profile = self.get_profile()
            except (TypeError, ValueError):
                self.cover_checkbox.setEnabled(False)
            else:
                self.cover_checkbox.setEnabled(profile.supports_thumbnail)


class AppShell(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("appShell")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(66)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 9, 22, 9)
        top_layout.setSpacing(10)

        brand_mark = QFrame()
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(36, 36)
        mark_layout = QHBoxLayout(brand_mark)
        mark_layout.setContentsMargins(8, 8, 8, 8)
        mark_icon = QLabel()
        mark_icon.setPixmap(QIcon(":/icons/music.svg").pixmap(20, 20))
        mark_layout.addWidget(mark_icon)
        top_layout.addWidget(brand_mark)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        wordmark = QLabel("Music Downloader")
        wordmark.setObjectName("wordmark")
        brand_text.addWidget(wordmark)
        brand_micro = QLabel("PREPARAR · REVISAR · SALVAR")
        brand_micro.setObjectName("brandMicro")
        brand_text.addWidget(brand_micro)
        top_layout.addLayout(brand_text)
        top_layout.addStretch(1)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(1)
        self.stage_label = QLabel("01 / 05 · ADICIONAR")
        self.stage_label.setObjectName("stageLabel")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        progress_layout.addWidget(self.stage_label)
        self.flow_rail = FlowRail()
        progress_layout.addWidget(self.flow_rail, alignment=Qt.AlignmentFlag.AlignRight)
        top_layout.addLayout(progress_layout)
        root.addWidget(top_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

    def set_stage(self, index: int, label: str) -> None:
        self.stage_label.setText(f"{index + 1:02d} / 05 · {label.upper()}")
        self.flow_rail.set_stage(index, label)


class AddPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(0)
        root.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        content = QWidget()
        content.setMaximumWidth(820)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        eyebrow = QLabel("FILA AUTORIZADA · YOUTUBE / CSV")
        eyebrow.setObjectName("eyebrow")
        content_layout.addWidget(eyebrow)
        title = QLabel("Adicionar músicas")
        title.setObjectName("pageTitle")
        content_layout.addWidget(title)
        subtitle = QLabel(
            "Cole músicas, vídeos ou playlists do YouTube. Separe vários itens com ponto e vírgula."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        input_header = QHBoxLayout()
        input_header.setContentsMargins(0, 5, 0, 0)
        input_label = QLabel("FAIXAS E LINKS")
        input_label.setObjectName("fieldLabel")
        input_header.addWidget(input_label)
        input_header.addStretch(1)
        self.input_summary_label = QLabel("Use ; para separar vários itens")
        self.input_summary_label.setObjectName("inputSummary")
        input_header.addWidget(self.input_summary_label)
        content_layout.addLayout(input_header)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setObjectName("universalInput")
        self.input_edit.setPlaceholderText(
            "Música - Artista; outra música - artista\nou https://youtube.com/…"
        )
        self.input_edit.setMinimumHeight(150)
        self.input_edit.setMaximumHeight(220)
        self.input_edit.setMaximumBlockCount(10000)
        input_label.setBuddy(self.input_edit)
        content_layout.addWidget(self.input_edit)

        self.notice = NoticeBanner()
        content_layout.addWidget(self.notice)

        destination_surface = QFrame()
        destination_surface.setObjectName("surface")
        destination_layout = QHBoxLayout(destination_surface)
        destination_layout.setContentsMargins(14, 10, 10, 10)
        destination_layout.setSpacing(10)
        folder_icon = QLabel()
        folder_icon.setPixmap(QIcon(":/icons/folder.svg").pixmap(20, 20))
        destination_layout.addWidget(folder_icon)
        destination_text = QVBoxLayout()
        destination_text.setSpacing(1)
        destination_title = QLabel("SALVAR EM")
        destination_title.setObjectName("outputLabel")
        destination_text.addWidget(destination_title)
        self.destination_edit = QLineEdit()
        self.destination_edit.setPlaceholderText("Escolha onde salvar os arquivos")
        self.destination_edit.setFrame(False)
        self.destination_edit.setStyleSheet("padding: 0; border: 0; background: transparent;")
        destination_text.addWidget(self.destination_edit)
        destination_layout.addLayout(destination_text, 1)
        self.browse_button = QPushButton("Escolher pasta")
        self.browse_button.setObjectName("secondaryButton")
        _set_button_icon(self.browse_button, "folder-open")
        destination_layout.addWidget(self.browse_button)
        content_layout.addWidget(destination_surface)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.import_button = QPushButton("Importar lista")
        self.options_button = QPushButton("MP3 · 192 kbps")
        self.import_button.setObjectName("secondaryButton")
        self.options_button.setObjectName("profileButton")
        self.import_button.setToolTip("Adicionar músicas de um CSV exportado do Spotify.")
        self.options_button.setToolTip(
            "Alterar tipo de mídia, formato, qualidade e sessão do YouTube."
        )
        _set_button_icon(self.import_button, "import")
        _set_button_icon(self.options_button, "sliders")
        actions.addWidget(self.import_button)
        actions.addWidget(self.options_button)
        actions.addStretch(1)
        self.search_button = QPushButton("Pesquisar músicas")
        self.search_button.setObjectName("primaryButton")
        self.search_button.setEnabled(False)
        self.search_button.setToolTip("Adicione pelo menos uma música ou link para pesquisar.")
        _set_button_icon(self.search_button, "search")
        actions.addWidget(self.search_button)
        content_layout.addLayout(actions)

        row.addWidget(content, 1)
        row.addStretch(1)
        root.addLayout(row)
        root.addStretch(1)

    def set_input_summary(self, count: int, duplicate_count: int = 0) -> None:
        if count == 0:
            text = "Use ; para separar vários itens"
        else:
            noun = "item pronto" if count == 1 else "itens prontos"
            text = f"{count} {noun}"
            if duplicate_count:
                duplicate_noun = (
                    "duplicata será ignorada"
                    if duplicate_count == 1
                    else "duplicatas serão ignoradas"
                )
                text += f" · {duplicate_count} {duplicate_noun}"
        self.input_summary_label.setText(text)
        self.input_summary_label.setProperty("ready", "true" if count else "false")
        self.input_summary_label.style().unpolish(self.input_summary_label)
        self.input_summary_label.style().polish(self.input_summary_label)

    def set_profile_summary(self, text: str) -> None:
        self.options_button.setText(text)


class SearchPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._total = 0
        self._found = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.addStretch(1)
        content = QWidget()
        content.setMaximumWidth(560)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        eyebrow = QLabel("ANÁLISE DA FILA")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(eyebrow)
        title = QLabel("Pesquisando músicas")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel("Comparando cada item com resultados do YouTube.")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        self.activity = QProgressBar()
        self.activity.setObjectName("activityProgress")
        self.activity.setRange(0, 1)
        self.activity.setValue(0)
        self.activity.setTextVisible(False)
        layout.addWidget(self.activity)
        self.found_label = QLabel("Preparando a fila…")
        self.found_label.setObjectName("secondaryText")
        self.found_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.found_label)
        self.notice = NoticeBanner()
        layout.addWidget(self.notice)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("dangerButton")
        _set_button_icon(self.cancel_button, "close")
        self.cancel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        cancel_row.addWidget(self.cancel_button)
        cancel_row.addStretch(1)
        layout.addLayout(cancel_row)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(content, 1)
        center.addStretch(1)
        root.addLayout(center)
        root.addStretch(1)

    def reset(self, total: int = 0) -> None:
        self._total = max(0, total)
        self._found = 0
        self.activity.setRange(0, max(1, self._total))
        self.activity.setValue(0)
        self._update_progress_text(0)
        self.notice.clear()

    def set_found_count(self, count: int) -> None:
        self._found = max(0, count)
        self._update_progress_text(self.activity.value())

    def set_progress(self, processed: int, total: int, found: int) -> None:
        self._total = max(0, total)
        self._found = max(0, found)
        self.activity.setRange(0, max(1, self._total))
        self.activity.setValue(min(max(0, processed), max(1, self._total)))
        self._update_progress_text(processed)

    def _update_progress_text(self, processed: int) -> None:
        if self._total <= 0:
            self.found_label.setText("Preparando a fila…")
            return
        analysed = "analisado" if self._total == 1 else "analisados"
        found = "1 encontrada" if self._found == 1 else f"{self._found} encontradas"
        self.found_label.setText(
            f"{min(max(0, processed), self._total)} de {self._total} {analysed} · {found}"
        )


_AUDIO_FORMAT_NAMES = {
    AudioFormat.AAC: "AAC",
    AudioFormat.ALAC: "ALAC",
    AudioFormat.FLAC: "FLAC",
    AudioFormat.M4A: "M4A",
    AudioFormat.MP3: "MP3",
    AudioFormat.OPUS: "Opus",
    AudioFormat.VORBIS: "Vorbis",
    AudioFormat.WAV: "WAV",
}

_VIDEO_FORMAT_NAMES = {
    VideoFormat.MP4_COMPATIBLE: "MP4 compatível",
    VideoFormat.MP4_FAST: "MP4 rápido",
    VideoFormat.WEBM: "WebM",
    VideoFormat.ORIGINAL: "Formato original",
}


def format_profile_summary(profile: DownloadProfile = DEFAULT_DOWNLOAD_PROFILE) -> str:
    """Return the compact output profile shown beside primary actions."""

    if profile.media_kind is MediaKind.AUDIO:
        fmt = _AUDIO_FORMAT_NAMES.get(profile.audio_format, "MP3")
        if profile.audio_bitrate_kbps is not None:
            return f"{fmt} · {profile.audio_bitrate_kbps} kbps"
        return fmt
    fmt = _VIDEO_FORMAT_NAMES.get(profile.video_format, "Vídeo")
    if profile.video_format is VideoFormat.ORIGINAL:
        return fmt
    resolution = (
        f"até {profile.max_video_height}p"
        if profile.max_video_height is not None
        else "melhor resolução"
    )
    return f"{fmt} · {resolution}"


def format_download_cta(
    selected: int, profile: DownloadProfile = DEFAULT_DOWNLOAD_PROFILE
) -> str:
    """Keep the primary action direct; output details live in the profile control."""

    if selected <= 0:
        return "Baixar seleção"
    if profile.media_kind is MediaKind.AUDIO:
        noun = "áudio" if selected == 1 else "áudios"
    else:
        noun = "vídeo" if selected == 1 else "vídeos"
    return f"Baixar {selected} {noun}"


class ReviewPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._profile_summary = format_profile_summary()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setText("Voltar à entrada")
        self.back_button.setObjectName("quietButton")
        _set_button_icon(self.back_button, "arrow-left")
        header.addWidget(self.back_button)
        header.addStretch(1)
        self.options_button = QPushButton(self._profile_summary)
        self.options_button.setObjectName("profileButton")
        self.options_button.setToolTip(
            "Alterar tipo de mídia, formato, qualidade e sessão do YouTube."
        )
        _set_button_icon(self.options_button, "sliders")
        header.addWidget(self.options_button)
        root.addLayout(header)

        title = QLabel("Revisar resultados")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        subtitle = QLabel(
            "Confira se as músicas encontradas estão corretas antes de baixar."
        )
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(subtitle)
        review_hint = QLabel(
            "Dê dois cliques em uma faixa para corrigir a busca antes do download."
        )
        review_hint.setObjectName("tertiaryText")
        root.addWidget(review_hint)

        actions = QHBoxLayout()
        self.summary_label = QLabel("Nenhum resultado")
        self.summary_label.setObjectName("secondaryText")
        actions.addWidget(self.summary_label)
        self.selection_label = QLabel("0 selecionadas")
        self.selection_label.setObjectName("selectionBadge")
        actions.addWidget(self.selection_label)
        actions.addStretch(1)
        self.select_found_button = QPushButton("Selecionar encontradas")
        self.clear_selection_button = QPushButton("Limpar seleção")
        self.more_button = QPushButton("Ações da faixa")
        for button in (self.select_found_button, self.clear_selection_button, self.more_button):
            button.setObjectName("quietButton")
        _set_button_icon(self.more_button, "more")
        self.more_button.setEnabled(False)
        actions.addWidget(self.select_found_button)
        actions.addWidget(self.clear_selection_button)
        actions.addWidget(self.more_button)
        root.addLayout(actions)

        self.notice = NoticeBanner()
        root.addWidget(self.notice)
        self.list_view = QListView()
        self.list_view.setObjectName("reviewList")
        self.list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.list_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setMouseTracking(True)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        root.addWidget(self.list_view, 1)

        self.editor = QFrame()
        self.editor.setObjectName("inlineEditor")
        editor_layout = QHBoxLayout(self.editor)
        editor_layout.setContentsMargins(12, 10, 10, 10)
        editor_layout.setSpacing(8)
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("Edite a busca desta música")
        self.research_button = QPushButton("Pesquisar novamente")
        self.research_button.setObjectName("primaryButton")
        self.editor_cancel_button = QPushButton("Cancelar")
        self.editor_cancel_button.setObjectName("quietButton")
        editor_layout.addWidget(self.query_edit, 1)
        editor_layout.addWidget(self.editor_cancel_button)
        editor_layout.addWidget(self.research_button)
        self.editor.hide()
        root.addWidget(self.editor)

        action_dock = QFrame()
        action_dock.setObjectName("actionDock")
        footer = QHBoxLayout(action_dock)
        footer.setContentsMargins(14, 10, 10, 10)
        footer.setSpacing(10)
        folder = QLabel()
        folder.setPixmap(QIcon(":/icons/folder.svg").pixmap(18, 18))
        footer.addWidget(folder)
        destination_text = QVBoxLayout()
        destination_text.setSpacing(1)
        destination_title = QLabel("SALVAR EM")
        destination_title.setObjectName("outputLabel")
        destination_text.addWidget(destination_title)
        self.destination_label = ElidedPathLabel("Destino não definido")
        self.destination_label.setObjectName("secondaryText")
        self.destination_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        destination_text.addWidget(self.destination_label)
        self.download_hint_label = QLabel("Escolha uma pasta para habilitar o download.")
        self.download_hint_label.setObjectName("downloadHint")
        destination_text.addWidget(self.download_hint_label)
        footer.addLayout(destination_text, 1)
        self.change_destination_button = QPushButton("Trocar pasta")
        self.change_destination_button.setObjectName("quietButton")
        _set_button_icon(self.change_destination_button, "folder-open")
        footer.addWidget(self.change_destination_button)
        self.download_button = QPushButton("Baixar seleção")
        self.download_button.setObjectName("primaryButton")
        self.download_button.setEnabled(False)
        _set_button_icon(self.download_button, "download")
        footer.addWidget(self.download_button)
        root.addWidget(action_dock)

    def update_summary(self, found: int, review: int) -> None:
        pieces = [f"{found} encontrada" if found == 1 else f"{found} encontradas"]
        if review:
            pieces.append(
                "1 precisa de revisão" if review == 1 else f"{review} precisam de revisão"
            )
        self.summary_label.setText("  ·  ".join(pieces))

    def update_selected_count(self, selected: int) -> None:
        noun = "selecionada" if selected == 1 else "selecionadas"
        self.selection_label.setText(f"{selected} {noun}")

    def set_profile_summary(self, text: str) -> None:
        self._profile_summary = text
        self.options_button.setText(text)

    def update_download_cta(
        self,
        selected: int,
        *,
        has_destination: bool,
        profile: DownloadProfile = DEFAULT_DOWNLOAD_PROFILE,
    ) -> None:
        cta_text = format_download_cta(selected, profile)
        profile_summary = format_profile_summary(profile)
        self.download_button.setText(cta_text)
        self.download_button.setToolTip(f"{cta_text} · {profile_summary}")
        self.download_button.setAccessibleName(f"{cta_text} em {profile_summary}")
        self.download_button.setEnabled(selected > 0 and has_destination)
        if selected <= 0:
            hint = "Selecione pelo menos uma faixa encontrada."
        elif not has_destination:
            hint = "Escolha a pasta de destino para baixar."
        else:
            hint = f"{profile_summary} · pronto para baixar"
        self.download_hint_label.setText(hint)

    def set_destination(self, destination: str) -> None:
        self.destination_label.set_path(destination)


class DownloadPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.addStretch(1)
        content = QWidget()
        content.setMaximumWidth(700)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        eyebrow = QLabel("DOWNLOAD EM ANDAMENTO")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("Salvando sua seleção")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.count_label = QLabel("0 de 0 concluídos")
        self.count_label.setObjectName("largeMetric")
        layout.addWidget(self.count_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        self.current_title = QLabel("Preparando downloads…")
        self.current_title.setObjectName("currentTrack")
        self.current_title.setWordWrap(True)
        layout.addWidget(self.current_title)
        self.status_label = QLabel("Preparando…")
        self.status_label.setObjectName("statusText")
        layout.addWidget(self.status_label)
        self.error_label = NoticeBanner()
        layout.addWidget(self.error_label)

        detail_header = QHBoxLayout()
        self.details_button = QPushButton("Mostrar log técnico")
        self.details_button.setObjectName("quietButton")
        _set_button_icon(self.details_button, "details")
        detail_header.addWidget(self.details_button)
        detail_header.addStretch(1)
        self.cancel_button = QPushButton("Cancelar download")
        self.cancel_button.setObjectName("dangerButton")
        _set_button_icon(self.cancel_button, "close")
        detail_header.addWidget(self.cancel_button)
        layout.addLayout(detail_header)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setObjectName("technicalLog")
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(500)
        self.log_edit.setMinimumHeight(150)
        self.log_edit.hide()
        layout.addWidget(self.log_edit)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(content, 1)
        center.addStretch(1)
        root.addLayout(center)
        root.addStretch(1)

    def reset(self, total: int) -> None:
        self.count_label.setText(f"0 de {total} concluídos")
        self.progress_bar.setValue(0)
        self.current_title.setText("Preparando downloads…")
        self.status_label.setText("Preparando…")
        self.error_label.clear()
        self.log_edit.clear()
        self.log_edit.hide()
        self.details_button.setText("Mostrar log técnico")

    def toggle_details(self) -> None:
        visible = not self.log_edit.isVisible()
        self.log_edit.setVisible(visible)
        self.details_button.setText(
            "Ocultar log técnico" if visible else "Mostrar log técnico"
        )


class CompletionPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.addStretch(1)
        content = QWidget()
        content.setMaximumWidth(620)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        eyebrow = QLabel("SESSÃO FINALIZADA")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(eyebrow)
        self.icon_label = QLabel()
        self.icon_label.setObjectName("successIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(QIcon(":/icons/success.svg").pixmap(28, 28))
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.title_label = QLabel("Download concluído")
        self.title_label.setObjectName("successTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("pageSubtitle")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.destination_label = QLabel("")
        self.destination_label.setObjectName("secondaryText")
        self.destination_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.destination_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.destination_label.setWordWrap(True)
        layout.addWidget(self.destination_label)
        self.failures_button = QPushButton()
        self.failures_button.setObjectName("quietButton")
        self.failures_button.hide()
        layout.addWidget(self.failures_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.failures_edit = QPlainTextEdit()
        self.failures_edit.setObjectName("technicalLog")
        self.failures_edit.setReadOnly(True)
        self.failures_edit.setMaximumHeight(170)
        self.failures_edit.hide()
        layout.addWidget(self.failures_edit)
        actions = QHBoxLayout()
        self.open_folder_button = QPushButton("Abrir pasta")
        self.open_folder_button.setObjectName("primaryButton")
        self.new_operation_button = QPushButton("Adicionar nova lista")
        self.new_operation_button.setObjectName("secondaryButton")
        _set_button_icon(self.open_folder_button, "folder-open-dark")
        _set_button_icon(self.new_operation_button, "refresh")
        actions.addWidget(self.open_folder_button)
        actions.addWidget(self.new_operation_button)
        layout.addLayout(actions)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(content, 1)
        center.addStretch(1)
        root.addLayout(center)
        root.addStretch(1)

    def show_result(
        self,
        *,
        successful: int,
        failed: int,
        cancelled: int,
        destination: str,
        failure_details: list[str],
        media_kind: MediaKind = MediaKind.AUDIO,
    ) -> None:
        if failed or cancelled:
            self.title_label.setText("Download finalizado")
            self.icon_label.setProperty("status", "partial")
            self.icon_label.setPixmap(QIcon(":/icons/warning.svg").pixmap(28, 28))
        else:
            self.title_label.setText("Download concluído")
            self.icon_label.setProperty("status", "success")
            self.icon_label.setPixmap(QIcon(":/icons/success.svg").pixmap(28, 28))
        self.icon_label.style().unpolish(self.icon_label)
        self.icon_label.style().polish(self.icon_label)
        if media_kind is MediaKind.VIDEO:
            noun = "vídeo foi baixado" if successful == 1 else "vídeos foram baixados"
        else:
            noun = "áudio foi baixado" if successful == 1 else "áudios foram baixados"
        self.summary_label.setText(f"{successful} {noun}")
        self.destination_label.setText(destination)
        self.destination_label.setToolTip(destination)
        self.open_folder_button.setEnabled(bool(destination) and Path(destination).exists())
        issue_count = failed + cancelled
        if issue_count:
            if media_kind is MediaKind.VIDEO:
                noun_issue = (
                    "vídeo não foi concluído"
                    if issue_count == 1
                    else "vídeos não foram concluídos"
                )
            else:
                noun_issue = (
                    "áudio não foi concluído"
                    if issue_count == 1
                    else "áudios não foram concluídos"
                )
            self.failures_button.setText(f"{issue_count} {noun_issue}  ›")
            self.failures_button.show()
            self.failures_edit.setPlainText("\n".join(failure_details))
            self.failures_edit.hide()
        else:
            self.failures_button.hide()
            self.failures_edit.clear()
            self.failures_edit.hide()

    def toggle_failures(self) -> None:
        self.failures_edit.setVisible(not self.failures_edit.isVisible())
