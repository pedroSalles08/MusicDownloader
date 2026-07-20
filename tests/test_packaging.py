from __future__ import annotations

from pathlib import Path
import tomllib

from music_downloader.app import create_argument_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_is_a_development_dependency() -> None:
    configuration = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))

    development = configuration["project"]["optional-dependencies"]["dev"]

    assert any(dependency.startswith("PyInstaller>=6.12") for dependency in development)


def test_spec_is_windowed_onedir_without_external_media_binaries() -> None:
    spec = (PROJECT_ROOT / "MusicDownloader.spec").read_text("utf-8")

    assert 'name="MusicDownloader"' in spec
    assert "console=False" in spec
    assert "exclude_binaries=True" in spec
    assert "COLLECT(" in spec
    assert 'binaries=[]' in spec
    assert "collect_submodules(\"yt_dlp\")" in spec
    assert 'module.startswith("yt_dlp.__pyinstaller")' in spec
    assert 'excludes=["PyInstaller", "pytest", "pytestqt", "setuptools", "tests"]' in spec
    assert "ffmpeg.exe" not in spec.casefold()
    assert "aria2c.exe" not in spec.casefold()
    assert "node.exe" not in spec.casefold()


def test_build_script_is_clean_reusable_and_checks_expected_exe() -> None:
    script = (PROJECT_ROOT / "packaging" / "build.ps1").read_text("utf-8")

    assert "[switch]$SkipInstall" in script
    assert "-m pip install -e" in script
    assert "-m PyInstaller" in script
    assert "--noconfirm" in script
    assert "--clean" in script
    assert "dist\\MusicDownloader\\MusicDownloader.exe" in script
    assert "Remove-Item" not in script


def test_entry_point_accepts_smoke_test_flag() -> None:
    arguments = create_argument_parser().parse_args(["--smoke-test"])

    assert arguments.smoke_test is True
