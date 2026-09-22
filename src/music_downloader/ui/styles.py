"""Midnight-deck visual system for the progressive desktop interface."""

from __future__ import annotations

BACKGROUND = "#0B0F14"
SURFACE = "#141A22"
SURFACE_HOVER = "#1B2430"
SEPARATOR = "#303B49"
TEXT_PRIMARY = "#F2EFE7"
TEXT_SECONDARY = "#B4BDC8"
TEXT_TERTIARY = "#7F8A98"
ACCENT = "#78A7FF"
ACCENT_HOVER = "#91B8FF"
ON_ACCENT = "#0A111B"
CUE = "#E7B56C"
SUCCESS = "#67C587"
WARNING = "#E7B56C"
ERROR = "#F07A77"

# Compatibility names kept for callers that imported the previous visual tokens.
BLUE = ACCENT
CREAM = BACKGROUND
PAPER = SURFACE

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 10pt;
}}
QLabel {{ background-color: transparent; }}
QWidget:disabled {{ color: {TEXT_TERTIARY}; }}
QFrame#appShell {{ background-color: {BACKGROUND}; }}
QFrame#topBar {{
    background-color: #0E131A;
    border-bottom: 1px solid {SEPARATOR};
}}
QFrame#brandMark {{
    background-color: #192433;
    border: 1px solid #3B5068;
    border-radius: 8px;
}}
QLabel#wordmark {{
    color: {TEXT_PRIMARY};
    font-size: 11pt;
    font-weight: 650;
}}
QLabel#brandMicro, QLabel#stageLabel, QLabel#eyebrow, QLabel#fieldLabel,
QLabel#outputLabel {{
    color: {TEXT_TERTIARY};
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 0.8px;
}}
QLabel#stageLabel {{ color: {TEXT_SECONDARY}; }}
QLabel#eyebrow {{ color: {CUE}; }}
QLabel#pageTitle {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 25pt;
    font-weight: 650;
}}
QLabel#pageSubtitle {{ color: {TEXT_SECONDARY}; font-size: 10.5pt; }}
QLabel#secondaryText {{ color: {TEXT_SECONDARY}; }}
QLabel#tertiaryText {{ color: {TEXT_TERTIARY}; }}
QLabel#sectionTitle {{ color: {TEXT_PRIMARY}; font-size: 11pt; font-weight: 600; }}
QLabel#largeMetric {{
    color: {TEXT_PRIMARY};
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 20pt;
    font-weight: 600;
}}
QLabel#currentTrack {{ color: {TEXT_PRIMARY}; font-size: 14pt; font-weight: 600; }}
QLabel#statusText {{ color: {TEXT_SECONDARY}; }}
QLabel#successTitle {{ color: {TEXT_PRIMARY}; font-size: 22pt; font-weight: 600; }}
QLabel#inputSummary {{
    color: {TEXT_SECONDARY};
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 8.5pt;
}}
QLabel#inputSummary[ready="true"] {{ color: #AFC8F7; }}
QLabel#selectionBadge {{
    color: #C9DAFF;
    background-color: #1B2A40;
    border: 1px solid #36537A;
    border-radius: 7px;
    padding: 4px 8px;
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 8.5pt;
    font-weight: 600;
}}
QLabel#downloadHint {{ color: {TEXT_TERTIARY}; font-size: 9pt; }}
QLabel#successIcon {{
    background-color: #142B22;
    border: 1px solid #326849;
    border-radius: 28px;
    min-width: 56px; max-width: 56px; min-height: 56px; max-height: 56px;
}}
QLabel#successIcon[status="partial"] {{
    background-color: #302415;
    border-color: #765A31;
}}
QLabel#noticeBanner {{
    background-color: #2A2116;
    color: #F6D29A;
    border: 1px solid #705431;
    border-radius: 8px;
    padding: 9px 12px;
}}
QLabel#noticeBanner[severity="error"] {{
    background-color: #2D191C;
    color: #FFC0BD;
    border-color: #75383B;
}}
QFrame#surface {{
    background-color: {SURFACE};
    border: 1px solid {SEPARATOR};
    border-radius: 10px;
}}
QFrame#sourceDeck {{
    background-color: #11171F;
    border: 1px solid {SEPARATOR};
    border-radius: 12px;
}}
QFrame#actionDock {{
    background-color: #11171F;
    border: 1px solid {SEPARATOR};
    border-radius: 11px;
}}
QFrame#inlineEditor {{
    background-color: {SURFACE_HOVER};
    border: 1px solid #465364;
    border-radius: 9px;
}}
QFrame#popover {{
    background-color: {SURFACE};
    border: 1px solid #465364;
    border-radius: 10px;
}}
QFrame#popoverDivider {{
    background-color: {SEPARATOR};
    max-height: 1px;
    border: 0;
}}
QLabel#losslessBadge {{
    color: {SUCCESS};
    background-color: #142B22;
    border: 1px solid #326849;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 9pt;
    font-weight: 600;
}}
QScrollArea {{
    background-color: transparent;
    border: 0;
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QWidget#popoverContent, QWidget#popoverSection, QWidget#popoverField {{
    background-color: transparent;
}}
QPlainTextEdit, QLineEdit, QComboBox {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid #3B4756;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QPlainTextEdit:hover, QLineEdit:hover, QComboBox:hover {{ border-color: #56677B; }}
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {ACCENT};
    padding: 7px 9px;
}}
QPlainTextEdit#universalInput {{
    background-color: #0F141B;
    font-size: 11.5pt;
    padding: 14px;
}}
QComboBox::drop-down {{ border: 0; width: 26px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #465364;
    selection-background-color: #2A4161;
    outline: 0;
}}
QPushButton, QToolButton {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #465364;
    border-radius: 8px;
    padding: 7px 13px;
    min-height: 24px;
}}
QPushButton:hover, QToolButton:hover {{ background-color: #25303D; border-color: #607185; }}
QPushButton:pressed, QToolButton:pressed {{ background-color: #2D3947; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {ACCENT}; }}
QPushButton:disabled, QToolButton:disabled {{
    background-color: #121820;
    color: #66717E;
    border-color: #28323E;
}}
QPushButton#primaryButton {{
    background-color: {ACCENT};
    color: {ON_ACCENT};
    border-color: {ACCENT};
    font-weight: 650;
    padding: 8px 16px;
}}
QPushButton#primaryButton:hover {{ background-color: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton#primaryButton:pressed {{ background-color: #6696EB; border-color: #6696EB; }}
QPushButton#primaryButton:disabled {{
    background-color: #26374D;
    color: #77879A;
    border-color: #26374D;
}}
QPushButton#secondaryButton {{
    background-color: #17202A;
    color: {TEXT_PRIMARY};
    border-color: #46576B;
}}
QPushButton#secondaryButton:hover {{ background-color: #202C39; border-color: #64788F; }}
QPushButton#profileButton {{
    background-color: #211D18;
    color: #F2CE98;
    border-color: #5D4A31;
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 9pt;
}}
QPushButton#profileButton:hover {{ background-color: #2B251C; border-color: #80643D; }}
QPushButton#quietButton, QToolButton#quietButton {{
    background-color: transparent;
    border-color: transparent;
    color: {TEXT_SECONDARY};
}}
QPushButton#quietButton:hover, QToolButton#quietButton:hover {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton#dangerButton {{
    background-color: transparent;
    color: #FFAAA6;
    border-color: #6C393C;
}}
QPushButton#dangerButton:hover {{ background-color: #2D191C; }}
QCheckBox {{ background-color: transparent; color: {TEXT_PRIMARY}; spacing: 9px; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #647184;
    border-radius: 4px;
    background-color: {SURFACE};
}}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    image: url(:/icons/check.svg);
}}
QListView#reviewList {{
    background-color: #11171F;
    border: 1px solid {SEPARATOR};
    border-radius: 11px;
    outline: 0;
}}
QListView#reviewList::item {{ border: 0; }}
QMenu {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #465364;
    padding: 6px;
}}
QMenu::item {{ padding: 7px 24px 7px 10px; border-radius: 5px; }}
QMenu::item:selected {{ background-color: #2A4161; }}
QProgressBar {{
    background-color: #242E3A;
    color: {TEXT_SECONDARY};
    border: 0;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 3px; }}
QProgressBar#activityProgress {{ min-height: 4px; max-height: 4px; }}
QPlainTextEdit#technicalLog {{
    background-color: #0D1218;
    color: #CDD4DC;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 9pt;
}}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #3F4B59; border-radius: 3px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: #586779; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{
    background-color: #222B36;
    color: {TEXT_PRIMARY};
    border: 1px solid #536174;
    padding: 5px;
}}
"""
