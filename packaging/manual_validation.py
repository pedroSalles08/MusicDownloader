"""Execute a controlled real download without retaining the generated media."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import traceback

from music_downloader.dependencies import detect_media_tools
from music_downloader.download_service import DownloadService
from music_downloader.models import DownloadBatchResult, DownloadStatus, SearchResult, SearchStatus
from music_downloader.search_service import SearchService


YOUTUBE_QUERY = "BaW_jenozKc youtube-dl test video"
YOUTUBE_ID = "BaW_jenozKc"
YOUTUBE_TITLE_FRAGMENT = "youtube-dl test video"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        """Keep validation output machine-readable."""


def _download_evidence(batch: DownloadBatchResult) -> dict[str, object]:
    result = batch.results[0] if batch.results else None
    output_path = result.output_path if result else None
    output_exists = bool(output_path and output_path.is_file())
    return {
        "preflight_error": batch.preflight_error,
        "status": result.status.value if result else None,
        "attempts": result.attempts if result else 0,
        "error": result.error if result else None,
        "output_name": output_path.name if output_path else None,
        "output_exists": output_exists,
        "output_bytes": output_path.stat().st_size if output_exists and output_path else 0,
    }


def _run_youtube(destination: Path) -> tuple[bool, dict[str, object]]:
    batch = SearchService().search_batch((YOUTUBE_QUERY,))
    result = batch.results[0]
    confirmed = (
        result.status is SearchStatus.FOUND
        and result.id == YOUTUBE_ID
        and result.title is not None
        and YOUTUBE_TITLE_FRAGMENT in result.title.casefold()
    )
    evidence: dict[str, object] = {
        "query": YOUTUBE_QUERY,
        "status": result.status.value,
        "id": result.id,
        "title": result.title,
        "url": result.url,
        "error": result.error,
        "metadata_confirmed": confirmed,
    }
    if not confirmed:
        evidence["download_skipped"] = (
            "O resultado não correspondeu ao vídeo público de teste esperado."
        )
        return False, evidence

    download = DownloadService().download_batch((result,), destination)
    download_evidence = _download_evidence(download)
    evidence["download"] = download_evidence
    success = (
        download_evidence["status"] == DownloadStatus.COMPLETED.value
        and bool(download_evidence["output_exists"])
    )
    return success, evidence


def _run_local_fallback(destination: Path) -> tuple[bool, dict[str, object]]:
    tools = detect_media_tools()
    evidence: dict[str, object] = {
        "ffmpeg": tools.ffmpeg.path,
        "ffprobe": tools.ffprobe.path,
    }
    if not tools.available or not tools.ffmpeg.path:
        evidence["error"] = tools.guidance
        return False, evidence

    source = destination / "authorized-test-tone.wav"
    command = [
        tools.ffmpeg.path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=1",
        "-c:a",
        "pcm_s16le",
        str(source),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        evidence["error"] = f"{type(error).__name__}: {error}"
        if isinstance(error, subprocess.CalledProcessError):
            evidence["ffmpeg_stderr"] = error.stderr.strip()
        return False, evidence

    handler = partial(_QuietHandler, directory=str(destination))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}/{source.name}"
        approved = SearchResult(
            query="tom local autorizado",
            status=SearchStatus.FOUND,
            title="Tom local autorizado",
            id="local-tone",
            url=url,
        )
        download = DownloadService().download_batch((approved,), destination)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    download_evidence = _download_evidence(download)
    evidence.update(
        {
            "source_bytes": source.stat().st_size,
            "server_stopped": not thread.is_alive(),
            "download": download_evidence,
        }
    )
    success = (
        download_evidence["status"] == DownloadStatus.COMPLETED.value
        and bool(download_evidence["output_exists"])
        and not thread.is_alive()
    )
    return success, evidence


def main() -> int:
    evidence: dict[str, object] = {}
    successful = False
    temporary = tempfile.TemporaryDirectory(prefix="music-downloader-validation-")
    root = Path(temporary.name)
    try:
        youtube_directory = root / "youtube"
        local_directory = root / "local"
        youtube_directory.mkdir()
        local_directory.mkdir()

        youtube_success, youtube_evidence = _run_youtube(youtube_directory)
        evidence["youtube"] = youtube_evidence
        if youtube_success:
            evidence["path_used"] = "youtube-controlled-test"
            successful = True
        else:
            local_success, local_evidence = _run_local_fallback(local_directory)
            evidence["local_fallback"] = local_evidence
            evidence["path_used"] = "localhost-authorized-tone"
            successful = local_success
    except Exception as error:
        evidence["unexpected_error"] = {
            "message": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
        }
    finally:
        temporary.cleanup()

    evidence["temporary_media_removed"] = not root.exists()
    evidence["successful"] = successful
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if successful and not root.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
