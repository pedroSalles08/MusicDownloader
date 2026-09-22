from __future__ import annotations

from pathlib import Path
import tomllib

from music_downloader.app import create_argument_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_is_a_development_dependency() -> None:
    configuration = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))

    development = configuration["project"]["optional-dependencies"]["dev"]

    assert any(dependency.startswith("PyInstaller>=6.12") for dependency in development)


def test_ytdlp_default_components_are_runtime_dependencies() -> None:
    configuration = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))

    runtime = configuration["project"]["dependencies"]

    assert any(dependency.startswith("yt-dlp[default]>=") for dependency in runtime)


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
    assert '$env:Path = "$env:SystemRoot\\System32;$env:SystemRoot"' in script


def test_entry_point_accepts_smoke_test_flag() -> None:
    arguments = create_argument_parser().parse_args(["--smoke-test"])

    assert arguments.smoke_test is True


def test_installer_registers_searchable_start_menu_shortcut() -> None:
    installer = (PROJECT_ROOT / "packaging" / "MusicDownloader.iss").read_text("utf-8")

    assert 'DefaultDirName={localappdata}\\Programs\\MusicDownloader' in installer
    assert 'Name: "{autoprograms}\\{#AppName}"' in installer
    assert 'IconFilename: "{app}\\{#AppExeName}"' in installer
    assert '#define AppUserModelID "PedroSalles08.MusicDownloader"' in installer
    assert 'AppUserModelID: "{#AppUserModelID}"' in installer
    assert 'Name: "desktopicon"' in installer
    assert 'Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked' not in installer
    assert "CurrentVersion\\App Paths\\{#AppExeName}" in installer
    assert "Classes\\Applications\\{#AppExeName}" in installer
    assert 'ValueName: "FriendlyAppName"; ValueData: "{#AppName}"' in installer
    assert "PrivilegesRequired=lowest" in installer
    assert "ChangesAssociations=yes" in installer
    assert 'Type: filesandordirs; Name: "{app}\\_internal"' in installer


def test_process_uses_same_explicit_windows_app_identity() -> None:
    app = (PROJECT_ROOT / "src" / "music_downloader" / "app.py").read_text("utf-8")

    assert 'APP_USER_MODEL_ID = "PedroSalles08.MusicDownloader"' in app
    assert "SetCurrentProcessExplicitAppUserModelID" in app
    assert app.index("set_windows_app_user_model_id()", app.index("def main")) < app.index(
        "QApplication.instance()", app.index("def main")
    )


def test_windows_executable_has_version_metadata() -> None:
    spec = (PROJECT_ROOT / "MusicDownloader.spec").read_text("utf-8")
    version_info = (PROJECT_ROOT / "packaging" / "version_info.txt").read_text("utf-8")
    configuration = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text("utf-8"))
    version = configuration["project"]["version"]
    windows_version = f"{version}.0"

    assert "version=str(VERSION_INFO)" in spec
    assert "StringStruct('FileDescription', 'Music Downloader')" in version_info
    assert "StringStruct('ProductName', 'Music Downloader')" in version_info
    assert f"StringStruct('ProductVersion', '{windows_version}')" in version_info
    assert f"StringStruct('FileVersion', '{windows_version}')" in version_info
    assert f"prodvers=({', '.join(version.split('.'))}, 0)" in version_info


def test_release_build_creates_installer_portable_zip_and_checksums() -> None:
    script = (PROJECT_ROOT / "packaging" / "build_release.ps1").read_text("utf-8")

    assert "Compress-Archive" in script
    assert "MusicDownloader-Setup-$version.exe" in script
    assert "MusicDownloader-$version-portable.zip" in script
    assert "SHA256SUMS.txt" in script
    assert "Get-FileHash" in script


def test_github_workflow_builds_and_publishes_tagged_releases() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text("utf-8")

    assert "tags:" in workflow
    assert '- "v*"' in workflow
    assert "python -m pytest -q" in workflow
    assert "build_release.ps1 -SkipTests" in workflow
    assert "build_release.ps1 -SkipInstall" not in workflow
    assert "gh release create" in workflow
    assert "gh release view" in workflow
    assert "gh release upload" in workflow
    assert "--clobber" in workflow
