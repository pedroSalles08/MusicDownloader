# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = Path(SPECPATH).resolve()
SOURCE_ROOT = PROJECT_ROOT / "src"

yt_dlp_hiddenimports = [
    module
    for module in collect_submodules("yt_dlp")
    if not module.startswith("yt_dlp.__pyinstaller")
]
yt_dlp_datas = collect_data_files("yt_dlp")

analysis = Analysis(
    [str(SOURCE_ROOT / "music_downloader" / "__main__.py")],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=yt_dlp_datas,
    hiddenimports=yt_dlp_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyInstaller", "pytest", "pytestqt", "setuptools", "tests"],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MusicDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

distribution = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MusicDownloader",
)
