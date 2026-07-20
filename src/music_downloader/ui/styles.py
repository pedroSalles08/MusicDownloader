"""Centralized palette and stylesheet for the retro desktop direction."""

from __future__ import annotations

CREAM = "#F4EBD8"
BEIGE = "#E4D5B7"
MINT = "#8FCDBF"
BLUE = "#3F6078"
GRAPHITE = "#263238"
PAPER = "#FFFDF7"
SUCCESS = "#417A5B"
WARNING = "#754315"
ERROR = "#A13D3D"

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {CREAM};
    color: {GRAPHITE};
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}}
QFrame#headerFrame {{
    background: {MINT};
    border: 2px solid {GRAPHITE};
    border-top-color: {PAPER};
    border-left-color: {PAPER};
}}
QLabel#appTitle {{
    font-family: Consolas, "Courier New", monospace;
    font-size: 20pt;
    font-weight: 700;
}}
QLabel#appSubtitle {{ color: #354F52; }}
QGroupBox {{
    background: {CREAM};
    border: 2px solid {GRAPHITE};
    border-radius: 3px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 2px 7px;
    background: {BLUE};
    color: {PAPER};
    font-family: Consolas, "Courier New", monospace;
}}
QPlainTextEdit, QLineEdit, QTableWidget {{
    background: {PAPER};
    border: 1px solid {GRAPHITE};
    selection-background-color: {BLUE};
    selection-color: {PAPER};
}}
QTableWidget {{ gridline-color: #8B8170; alternate-background-color: #F0E4CC; }}
QHeaderView::section {{
    background: {BEIGE};
    border: 1px solid {GRAPHITE};
    padding: 4px;
    font-family: Consolas, "Courier New", monospace;
    font-weight: 600;
}}
QPushButton {{
    background: {BEIGE};
    border: 2px solid {GRAPHITE};
    border-top-color: {PAPER};
    border-left-color: {PAPER};
    padding: 5px 10px;
    min-height: 20px;
}}
QPushButton:hover {{ background: {MINT}; }}
QPushButton:pressed {{
    background: #CDBE9F;
    border-top-color: {GRAPHITE};
    border-left-color: {GRAPHITE};
}}
QPushButton:disabled {{ color: #77736B; background: #D8D0C0; }}
QPushButton#primaryButton {{ background: {BLUE}; color: {PAPER}; font-weight: 700; }}
QPushButton#dangerButton {{ background: #D8A29D; }}
QProgressBar {{
    background: {PAPER};
    border: 1px solid {GRAPHITE};
    text-align: center;
}}
QProgressBar::chunk {{ background: {MINT}; }}
QStatusBar {{ background: {BEIGE}; border-top: 1px solid {GRAPHITE}; }}
QLabel#spotifyHint {{ color: {WARNING}; }}
QLabel#summaryLabel {{
    background: {BEIGE};
    border: 1px solid {GRAPHITE};
    padding: 5px;
    font-family: Consolas, "Courier New", monospace;
}}
"""
