"""Application bootstrap kept separate for tests and packaging."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from music_downloader.ui.main_window import MainWindow


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Music Downloader desktop")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Abre e fecha a janela sem iniciar operações de rede.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_argument_parser().parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Music Downloader")
    window = MainWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(100, window.close)
        QTimer.singleShot(150, app.quit)
    return app.exec()
