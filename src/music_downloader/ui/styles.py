"""Dark visual system for the progressive desktop interface."""

from __future__ import annotations

BACKGROUND = "#0E0E10"
SURFACE = "#17171A"
SURFACE_HOVER = "#202025"
SEPARATOR = "#2C2C2E"
TEXT_PRIMARY = "#F5F5F7"
TEXT_SECONDARY = "#A1A1A6"
TEXT_TERTIARY = "#6E6E73"
ACCENT = "#0A84FF"
ACCENT_HOVER = "#3395FF"
SUCCESS = "#32D74B"
WARNING = "#FF9F0A"
ERROR = "#FF453A"

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
    background-color: {BACKGROUND};
    border-bottom: 1px solid {SEPARATOR};
}}
QLabel#wordmark {{
    color: {TEXT_PRIMARY};
    font-size: 11pt;
    font-weight: 600;
}}
QLabel#pageTitle {{
    color: {TEXT_PRIMARY};
    font-size: 24pt;
    font-weight: 600;
}}
QLabel#pageSubtitle {{ color: {TEXT_SECONDARY}; font-size: 10.5pt; }}
QLabel#secondaryText {{ color: {TEXT_SECONDARY}; }}
QLabel#tertiaryText {{ color: {TEXT_TERTIARY}; }}
QLabel#sectionTitle {{ color: {TEXT_PRIMARY}; font-size: 11pt; font-weight: 600; }}
QLabel#largeMetric {{ color: {TEXT_PRIMARY}; font-size: 22pt; font-weight: 600; }}
QLabel#currentTrack {{ color: {TEXT_PRIMARY}; font-size: 14pt; font-weight: 600; }}
QLabel#statusText {{ color: {TEXT_SECONDARY}; }}
QLabel#successTitle {{ color: {TEXT_PRIMARY}; font-size: 22pt; font-weight: 600; }}
QLabel#successIcon {{
    background-color: #15351F;
    border: 1px solid #246936;
    border-radius: 28px;
    min-width: 56px; max-width: 56px; min-height: 56px; max-height: 56px;
}}
QLabel#successIcon[status="partial"] {{
    background-color: #36270F;
    border-color: #76551B;
}}
QLabel#noticeBanner {{
    background-color: #242018;
    color: #FFD18A;
    border: 1px solid #5D4725;
    border-radius: 8px;
    padding: 9px 12px;
}}
QLabel#noticeBanner[severity="error"] {{
    background-color: #2A1719;
    color: #FFB4AC;
    border-color: #6B2B30;
}}
QFrame#surface {{
    background-color: {SURFACE};
    border: 1px solid {SEPARATOR};
    border-radius: 11px;
}}
QFrame#inlineEditor {{
    background-color: {SURFACE_HOVER};
    border: 1px solid #3A3A40;
    border-radius: 9px;
}}
QFrame#popover {{
    background-color: {SURFACE};
    border: 1px solid #3A3A40;
    border-radius: 10px;
}}
QFrame#popoverDivider {{
    background-color: {SEPARATOR};
    max-height: 1px;
    border: 0;
}}
QLabel#losslessBadge {{
    color: {SUCCESS};
    background-color: #15351F;
    border: 1px solid #246936;
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
    border: 1px solid #3A3A40;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QPlainTextEdit:hover, QLineEdit:hover, QComboBox:hover {{ border-color: #505058; }}
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {ACCENT};
    padding: 7px 9px;
}}
QPlainTextEdit#universalInput {{ font-size: 11.5pt; padding: 14px; }}
QComboBox::drop-down {{ border: 0; width: 26px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #3A3A40;
    selection-background-color: #263D59;
    outline: 0;
}}
QPushButton, QToolButton {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #3A3A40;
    border-radius: 8px;
    padding: 7px 13px;
    min-height: 22px;
}}
QPushButton:hover, QToolButton:hover {{ background-color: #29292F; border-color: #505058; }}
QPushButton:pressed, QToolButton:pressed {{ background-color: #323238; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {ACCENT}; }}
QPushButton:disabled, QToolButton:disabled {{
    background-color: #18181B;
    color: #59595F;
    border-color: #28282D;
}}
QPushButton#primaryButton {{
    background-color: {ACCENT};
    color: white;
    border-color: {ACCENT};
    font-weight: 600;
    padding: 8px 16px;
}}
QPushButton#primaryButton:hover {{ background-color: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton#primaryButton:pressed {{ background-color: #0874DE; }}
QPushButton#primaryButton:disabled {{
    background-color: #1B4770;
    color: #7F9AB5;
    border-color: #1B4770;
}}
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
    color: #FF817A;
    border-color: #633033;
}}
QPushButton#dangerButton:hover {{ background-color: #2A1719; }}
QCheckBox {{ background-color: transparent; color: {TEXT_PRIMARY}; spacing: 9px; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #5B5B63;
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
    background-color: {SURFACE};
    border: 1px solid {SEPARATOR};
    border-radius: 11px;
    outline: 0;
}}
QListView#reviewList::item {{ border: 0; }}
QMenu {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #3A3A40;
    padding: 6px;
}}
QMenu::item {{ padding: 7px 24px 7px 10px; border-radius: 5px; }}
QMenu::item:selected {{ background-color: #2B4463; }}
QProgressBar {{
    background-color: #242429;
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
    background-color: #111113;
    color: #C7C7CC;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 9pt;
}}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 3px; }}
QScrollBar::handle:vertical {{ background: #3A3A40; border-radius: 3px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: #505058; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{
    background-color: #27272C;
    color: {TEXT_PRIMARY};
    border: 1px solid #46464D;
    padding: 5px;
}}
"""
