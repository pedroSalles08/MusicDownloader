"""Sequential, retrying yt-dlp download service with cooperative cancellation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import hashlib
from pathlib import Path
from typing import Any

import yt_dlp

from music_downloader.browser_cookies import SUPPORTED_COOKIE_BROWSERS
from music_downloader.cancellation import CancellationToken, OperationCancelled
from music_downloader.dependencies import detect_media_tools
from music_downloader.diagnostics import exception_diagnostic
from music_downloader.download_profiles import (
    DEFAULT_DOWNLOAD_PROFILE,
    AudioFormat,
    DownloadProfile,
    MediaKind,
    VideoFormat,
)
from music_downloader.models import (
    DownloadBatchResult,
    DownloadProgress,
    DownloadProgressStatus,
    DownloadResult,
    DownloadStatus,
    MediaToolsStatus,
    SearchResult,
    SearchStatus,
)
from music_downloader.windows_paths import sanitize_windows_filename
from music_downloader.ytdlp_types import YoutubeDLFactory, default_ytdl_factory

DownloadProgressCallback = Callable[[DownloadProgress], None]
ToolDetector = Callable[[], MediaToolsStatus]
RetryWaiter = Callable[[float, CancellationToken], None]

_MAX_BASENAME_UTF16_UNITS = 240


def _utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def _default_waiter(delay: float, token: CancellationToken) -> None:
    if token.wait(delay):
        token.raise_if_cancelled()


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="surrogatepass")).hexdigest()[:8]


def build_output_basename(
    result: SearchResult, *, ordinal: int | None = None
) -> str:
    """Build a safe title that keeps a stable media identifier suffix."""

    raw_id = result.id
    if not raw_id:
        raw_id = _stable_hash(result.url or result.query)
    safe_id = sanitize_windows_filename(raw_id, max_length=48, fallback="item")
    if safe_id != raw_id:
        safe_id = sanitize_windows_filename(
            f"{safe_id}-{_stable_hash(raw_id)}", max_length=57, fallback="item"
        )
    ordinal_suffix = f" ({ordinal})" if ordinal is not None else ""
    suffix = f" [{safe_id}]{ordinal_suffix}"
    title_budget = _MAX_BASENAME_UTF16_UNITS - _utf16_units(suffix)
    safe_title = sanitize_windows_filename(
        result.title or result.query,
        max_length=max(1, title_budget),
        fallback="audio",
    )
    return sanitize_windows_filename(
        f"{safe_title}{suffix}",
        max_length=_MAX_BASENAME_UTF16_UNITS,
        fallback=f"audio{suffix}",
    )


def _reserve_output_basename(
    result: SearchResult,
    *,
    existing_names: tuple[str, ...],
    reserved_basenames: set[str],
) -> str:
    ordinal: int | None = None
    while True:
        candidate = build_output_basename(result, ordinal=ordinal)
        key = candidate.casefold()
        exists_on_disk = any(
            name == key or name.startswith(f"{key}.") for name in existing_names
        )
        if key not in reserved_basenames and not exists_on_disk:
            reserved_basenames.add(key)
            return candidate
        ordinal = 2 if ordinal is None else ordinal + 1


def download_options(
    output_template: Path,
    *,
    profile: DownloadProfile = DEFAULT_DOWNLOAD_PROFILE,
    embed_thumbnail: bool,
    aria2c_path: str | None,
    cookie_browser: str | None,
    progress_hook: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    """Return structured yt-dlp options for one validated output profile."""

    postprocessors: list[dict[str, Any]] = []
    if profile.media_kind is MediaKind.AUDIO:
        assert profile.audio_format is not None
        extract_audio: dict[str, Any] = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": profile.audio_format.value,
        }
        if profile.audio_bitrate_kbps is not None:
            extract_audio["preferredquality"] = str(profile.audio_bitrate_kbps)
        postprocessors.append(extract_audio)
        format_selector = "bestaudio/best"
    else:
        assert profile.video_format is not None
        height_filter = (
            "" if profile.max_video_height is None else f"[height<=?{profile.max_video_height}]"
        )
        if profile.video_format is VideoFormat.MP4_COMPATIBLE:
            format_selector = f"bestvideo{height_filter}+bestaudio"
            postprocessors.append(
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            )
        elif profile.video_format is VideoFormat.MP4_FAST:
            format_selector = (
                f"bestvideo[ext=mp4]{height_filter}+bestaudio[ext=m4a]"
                f"/best[ext=mp4]{height_filter}"
            )
        elif profile.video_format is VideoFormat.WEBM:
            format_selector = (
                f"bestvideo[ext=webm]{height_filter}+bestaudio[ext=webm]"
                f"/best[ext=webm]{height_filter}"
            )
        else:
            format_selector = f"bestvideo*{height_filter}+bestaudio/best{height_filter}"

    postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if embed_thumbnail:
        postprocessors.append({"key": "EmbedThumbnail"})

    options: dict[str, Any] = {
        "format": format_selector,
        "outtmpl": str(output_template),
        "noplaylist": True,
        "js_runtimes": {"node": {}},
        "continuedl": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 8,
        "socket_timeout": 30,
        "writethumbnail": embed_thumbnail,
        "postprocessors": postprocessors,
        "progress_hooks": [progress_hook],
    }
    if profile.output_extension:
        options["final_ext"] = profile.output_extension
    if profile.video_format is VideoFormat.MP4_COMPATIBLE:
        # Force an intermediate container so the converter always runs. Its
        # output arguments replace stream-copy with broadly compatible codecs.
        options["merge_output_format"] = "mkv"
        options["postprocessor_args"] = {
            "videoconvertor+ffmpeg_o": [
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
            ]
        }
    elif profile.video_format is VideoFormat.MP4_FAST:
        options["merge_output_format"] = "mp4"
    elif profile.video_format is VideoFormat.WEBM:
        options["merge_output_format"] = "webm"
    if aria2c_path:
        options["external_downloader"] = aria2c_path
        options["external_downloader_args"] = {"aria2c": ["-k", "1M"]}
    if cookie_browser:
        options["cookiesfrombrowser"] = (cookie_browser,)
    return options


def _is_youtube_auth_error(error: Exception) -> bool:
    diagnostic = str(error).casefold()
    return (
        "sign in to confirm you're not a bot" in diagnostic
        or "sign in to confirm you’re not a bot" in diagnostic
    )


def _is_requested_format_error(error: Exception) -> bool:
    return "requested format is not available" in str(error).casefold()


def _is_non_retryable_download_error(error: Exception) -> bool:
    diagnostic = str(error).casefold()
    return (
        _is_youtube_auth_error(error)
        or _is_requested_format_error(error)
        or "video unavailable" in diagnostic
    )


def _download_error_diagnostic(
    error: Exception, *, cookie_browser: str | None
) -> str:
    if _is_youtube_auth_error(error):
        if cookie_browser:
            return (
                "O YouTube recusou a sessão do navegador selecionado. Confirme que "
                "você está conectado ao YouTube nesse navegador; se necessário, "
                "feche o navegador ou selecione outro e tente novamente."
            )
        return (
            "O YouTube pediu autenticação anti-bot. Selecione em ‘Sessão YouTube’ "
            "um navegador no qual você esteja conectado ao YouTube e tente "
            "novamente."
        )
    if _is_requested_format_error(error):
        return (
            "O YouTube não forneceu um formato de mídia compatível com o perfil. "
            "Tente outra qualidade ou formato. Atualize o "
            "aplicativo para uma versão com os componentes JavaScript EJS; se o "
            "problema continuar em um vídeo específico, ele pode exigir PO Token."
        )
    return exception_diagnostic(error)


class DownloadService:
    def __init__(
        self,
        ytdl_factory: YoutubeDLFactory = default_ytdl_factory,
        *,
        tool_detector: ToolDetector = detect_media_tools,
        waiter: RetryWaiter = _default_waiter,
        transient_errors: tuple[type[Exception], ...] = (yt_dlp.utils.DownloadError,),
        retry_delays: tuple[float, ...] = (2.0, 5.0),
    ) -> None:
        self._ytdl_factory = ytdl_factory
        self._tool_detector = tool_detector
        self._waiter = waiter
        self._transient_errors = transient_errors
        self._retry_delays = retry_delays

    def download_batch(
        self,
        approved_results: Iterable[SearchResult],
        output_directory: str | Path,
        *,
        profile: DownloadProfile = DEFAULT_DOWNLOAD_PROFILE,
        embed_thumbnail: bool = False,
        aria2c_path: str | None = None,
        cookie_browser: str | None = None,
        cancellation: CancellationToken | None = None,
        progress_callback: DownloadProgressCallback | None = None,
    ) -> DownloadBatchResult:
        """Download approved direct URLs, continuing after individual failures."""

        token = cancellation or CancellationToken()
        items = tuple(approved_results)
        if not items:
            return DownloadBatchResult(results=(), cancelled=token.cancelled)
        if token.cancelled:
            return DownloadBatchResult(results=(), cancelled=True)
        if embed_thumbnail and not profile.supports_thumbnail:
            return DownloadBatchResult(
                results=(),
                cancelled=False,
                preflight_error=(
                    "O perfil selecionado não permite incorporar thumbnail. "
                    "Desative a capa ou escolha outro formato."
                ),
            )
        if (
            cookie_browser not in SUPPORTED_COOKIE_BROWSERS
            and cookie_browser is not None
        ):
            return DownloadBatchResult(
                results=(),
                cancelled=False,
                preflight_error="Navegador inválido para carregar a sessão do YouTube.",
            )

        try:
            tools = self._tool_detector()
        except Exception as error:
            return DownloadBatchResult(
                results=(),
                cancelled=False,
                preflight_error=exception_diagnostic(error),
            )
        if not tools.available:
            return DownloadBatchResult(
                results=(), cancelled=False, preflight_error=tools.guidance
            )

        try:
            destination = Path(output_directory)
            destination.mkdir(parents=True, exist_ok=True)
            existing_names = tuple(entry.name.casefold() for entry in destination.iterdir())
        except (OSError, TypeError, ValueError) as error:
            return DownloadBatchResult(
                results=(),
                cancelled=False,
                preflight_error=exception_diagnostic(error),
            )

        outcomes: list[DownloadResult] = []
        reserved_basenames: set[str] = set()
        for item_index, item in enumerate(items, start=1):
            if token.cancelled:
                break

            basename = None
            if item.status is SearchStatus.FOUND and item.url:
                basename = _reserve_output_basename(
                    item,
                    existing_names=existing_names,
                    reserved_basenames=reserved_basenames,
                )
            outcome = self._download_one(
                item,
                item_index=item_index,
                total_items=len(items),
                processed_items=len(outcomes),
                destination=destination,
                profile=profile,
                embed_thumbnail=embed_thumbnail,
                aria2c_path=aria2c_path,
                cookie_browser=cookie_browser,
                token=token,
                progress_callback=progress_callback,
                basename=basename,
            )
            outcomes.append(outcome)
            if token.cancelled:
                break

        return DownloadBatchResult(
            results=tuple(outcomes),
            cancelled=token.cancelled,
        )

    def _download_one(
        self,
        item: SearchResult,
        *,
        item_index: int,
        total_items: int,
        processed_items: int,
        destination: Path,
        profile: DownloadProfile,
        embed_thumbnail: bool,
        aria2c_path: str | None,
        cookie_browser: str | None,
        token: CancellationToken,
        progress_callback: DownloadProgressCallback | None,
        basename: str | None,
    ) -> DownloadResult:
        if item.status is not SearchStatus.FOUND or not item.url:
            error = "O item aprovado não possui um resultado encontrado com URL direta."
            self._emit_progress(
                item,
                item_index,
                total_items,
                processed_items + 1,
                DownloadProgressStatus.ERROR,
                progress_callback,
            )
            return DownloadResult(
                query=item.query,
                id=item.id,
                status=DownloadStatus.ERROR,
                output_path=None,
                attempts=0,
                error=error,
            )

        if basename is None:
            raise AssertionError("valid download item requires a reserved basename")
        output_path = (
            destination / f"{basename}.{profile.output_extension}"
            if profile.output_extension
            else None
        )
        output_template = destination / f"{basename}.%(ext)s"
        attempt_limit = min(3, len(self._retry_delays) + 1)

        def hook(data: dict[str, Any]) -> None:
            token.raise_if_cancelled()
            hook_status = data.get("status")
            status = (
                DownloadProgressStatus.PROCESSING
                if hook_status == "finished"
                else DownloadProgressStatus.DOWNLOADING
            )
            downloaded = self._optional_int(data.get("downloaded_bytes"))
            total = self._optional_int(data.get("total_bytes")) or self._optional_int(
                data.get("total_bytes_estimate")
            )
            fraction = None
            if downloaded is not None and total:
                fraction = min(1.0, max(0.0, downloaded / total))
            self._emit_progress(
                item,
                item_index,
                total_items,
                processed_items,
                status,
                progress_callback,
                item_fraction=fraction,
                downloaded_bytes=downloaded,
                total_bytes=total,
            )
            token.raise_if_cancelled()

        options = download_options(
            output_template,
            profile=profile,
            embed_thumbnail=embed_thumbnail,
            aria2c_path=aria2c_path,
            cookie_browser=cookie_browser,
            progress_hook=hook,
        )

        for attempt in range(1, attempt_limit + 1):
            try:
                token.raise_if_cancelled()
                with self._ytdl_factory(options) as ydl:
                    info = ydl.extract_info(item.url, download=True)
                token.raise_if_cancelled()
                actual_output_path = self._result_output_path(info, output_path)
                self._emit_progress(
                    item,
                    item_index,
                    total_items,
                    processed_items + 1,
                    DownloadProgressStatus.COMPLETED,
                    progress_callback,
                    item_fraction=1.0,
                )
                return DownloadResult(
                    query=item.query,
                    id=item.id,
                    status=DownloadStatus.COMPLETED,
                    output_path=actual_output_path,
                    attempts=attempt,
                )
            except OperationCancelled as error:
                self._emit_progress(
                    item,
                    item_index,
                    total_items,
                    processed_items + 1,
                    DownloadProgressStatus.CANCELLED,
                    progress_callback,
                )
                return DownloadResult(
                    query=item.query,
                    id=item.id,
                    status=DownloadStatus.CANCELLED,
                    output_path=None,
                    attempts=attempt,
                    error=str(error),
                )
            except self._transient_errors as error:
                if token.cancelled:
                    self._emit_progress(
                        item,
                        item_index,
                        total_items,
                        processed_items + 1,
                        DownloadProgressStatus.CANCELLED,
                        progress_callback,
                    )
                    return DownloadResult(
                        query=item.query,
                        id=item.id,
                        status=DownloadStatus.CANCELLED,
                        output_path=None,
                        attempts=attempt,
                        error="Operação cancelada pelo usuário.",
                    )
                if _is_non_retryable_download_error(error):
                    return self._error_result(
                        item,
                        attempt,
                        error,
                        item_index,
                        total_items,
                        processed_items,
                        progress_callback,
                        cookie_browser=cookie_browser,
                    )
                if attempt == attempt_limit:
                    return self._error_result(
                        item,
                        attempt,
                        error,
                        item_index,
                        total_items,
                        processed_items,
                        progress_callback,
                        cookie_browser=cookie_browser,
                    )
                self._emit_progress(
                    item,
                    item_index,
                    total_items,
                    processed_items,
                    DownloadProgressStatus.RETRYING,
                    progress_callback,
                )
                try:
                    self._waiter(self._retry_delays[attempt - 1], token)
                    token.raise_if_cancelled()
                except OperationCancelled as cancellation_error:
                    self._emit_progress(
                        item,
                        item_index,
                        total_items,
                        processed_items + 1,
                        DownloadProgressStatus.CANCELLED,
                        progress_callback,
                    )
                    return DownloadResult(
                        query=item.query,
                        id=item.id,
                        status=DownloadStatus.CANCELLED,
                        output_path=None,
                        attempts=attempt,
                        error=str(cancellation_error),
                    )
            except Exception as error:
                return self._error_result(
                    item,
                    attempt,
                    error,
                    item_index,
                    total_items,
                    processed_items,
                    progress_callback,
                    cookie_browser=cookie_browser,
                )

        raise AssertionError("unreachable")

    @staticmethod
    def _result_output_path(
        info: object, fallback: Path | None
    ) -> Path | None:
        if isinstance(info, Mapping):
            filepath = info.get("filepath")
            if isinstance(filepath, str) and filepath:
                return Path(filepath)
        return fallback

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return int(value)

    @staticmethod
    def _emit_progress(
        item: SearchResult,
        item_index: int,
        total_items: int,
        processed_items: int,
        status: DownloadProgressStatus,
        callback: DownloadProgressCallback | None,
        *,
        item_fraction: float | None = None,
        downloaded_bytes: int | None = None,
        total_bytes: int | None = None,
    ) -> None:
        if callback:
            callback(
                DownloadProgress(
                    query=item.query,
                    id=item.id,
                    item_index=item_index,
                    total_items=total_items,
                    processed_items=processed_items,
                    status=status,
                    item_fraction=item_fraction,
                    downloaded_bytes=downloaded_bytes,
                    total_bytes=total_bytes,
                )
            )

    def _error_result(
        self,
        item: SearchResult,
        attempt: int,
        error: Exception,
        item_index: int,
        total_items: int,
        processed_items: int,
        callback: DownloadProgressCallback | None,
        *,
        cookie_browser: str | None,
    ) -> DownloadResult:
        self._emit_progress(
            item,
            item_index,
            total_items,
            processed_items + 1,
            DownloadProgressStatus.ERROR,
            callback,
        )
        return DownloadResult(
            query=item.query,
            id=item.id,
            status=DownloadStatus.ERROR,
            output_path=None,
            attempts=attempt,
            error=_download_error_diagnostic(error, cookie_browser=cookie_browser),
        )
