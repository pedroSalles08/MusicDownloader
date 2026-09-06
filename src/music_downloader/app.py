"""Application bootstrap kept separate for tests and packaging."""

from __future__ import annotations

import argparse
import ctypes
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication

from music_downloader.ui.main_window import MainWindow


APP_USER_MODEL_ID = "PedroSalles08.MusicDownloader"


def set_windows_app_user_model_id() -> None:
    """Assign the stable identity also stored in the installed shortcut."""
    if sys.platform != "win32":
        return

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    setter = shell32.SetCurrentProcessExplicitAppUserModelID
    setter.argtypes = [ctypes.c_wchar_p]
    setter.restype = ctypes.c_long
    result = setter(APP_USER_MODEL_ID)
    if result < 0:
        raise OSError(result, "Não foi possível definir a identidade do aplicativo.")


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
    set_windows_app_user_model_id()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Music Downloader")
    app.setApplicationDisplayName("Music Downloader")
    app.setOrganizationName("pedroSalles08")
    style_hints = app.styleHints()
    if hasattr(style_hints, "setColorScheme"):
        style_hints.setColorScheme(Qt.ColorScheme.Dark)
    window = MainWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(100, window.close)
        QTimer.singleShot(150, app.quit)
    return app.exec()
