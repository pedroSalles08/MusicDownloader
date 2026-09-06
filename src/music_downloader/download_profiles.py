"""Validated output profiles shared by the download service and the UI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MediaKind(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


class AudioFormat(str, Enum):
    AAC = "aac"
    ALAC = "alac"
    FLAC = "flac"
    M4A = "m4a"
    MP3 = "mp3"
    OPUS = "opus"
    VORBIS = "vorbis"
    WAV = "wav"


class VideoFormat(str, Enum):
    MP4_COMPATIBLE = "mp4_compatible"
    MP4_FAST = "mp4_fast"
    WEBM = "webm"
    ORIGINAL = "original"


AUDIO_BITRATE_CHOICES = (128, 192, 256, 320)
VIDEO_HEIGHT_CHOICES = (360, 720, 1080)

_LOSSLESS_AUDIO_FORMATS = frozenset(
    {AudioFormat.ALAC, AudioFormat.FLAC, AudioFormat.WAV}
)
_AUDIO_OUTPUT_EXTENSIONS = {
    AudioFormat.AAC: "m4a",
    AudioFormat.ALAC: "m4a",
    AudioFormat.FLAC: "flac",
    AudioFormat.M4A: "m4a",
    AudioFormat.MP3: "mp3",
    AudioFormat.OPUS: "opus",
    AudioFormat.VORBIS: "ogg",
    AudioFormat.WAV: "wav",
}


@dataclass(frozen=True, slots=True)
class DownloadProfile:
    """One validated, UI-safe media output configuration.

    The application deliberately exposes a closed set of profiles instead of
    accepting arbitrary yt-dlp selectors or FFmpeg arguments from users.
    """

    media_kind: MediaKind
    audio_format: AudioFormat | None = None
    audio_bitrate_kbps: int | None = None
    video_format: VideoFormat | None = None
    max_video_height: int | None = None

    def __post_init__(self) -> None:
        if self.media_kind is MediaKind.AUDIO:
            if self.audio_format is None or self.video_format is not None:
                raise ValueError("Um perfil de áudio exige somente audio_format.")
            if self.max_video_height is not None:
                raise ValueError("Um perfil de áudio não aceita resolução de vídeo.")
            if self.audio_format in _LOSSLESS_AUDIO_FORMATS:
                if self.audio_bitrate_kbps is not None:
                    raise ValueError(
                        "Formatos de áudio sem perdas não aceitam bitrate configurável."
                    )
            elif self.audio_bitrate_kbps not in AUDIO_BITRATE_CHOICES:
                raise ValueError(
                    "O bitrate deve ser 128, 192, 256 ou 320 kbps."
                )
            return

        if self.media_kind is MediaKind.VIDEO:
            if self.video_format is None or self.audio_format is not None:
                raise ValueError("Um perfil de vídeo exige somente video_format.")
            if self.audio_bitrate_kbps is not None:
                raise ValueError("Um perfil de vídeo não aceita bitrate de áudio.")
            if (
                self.max_video_height is not None
                and self.max_video_height not in VIDEO_HEIGHT_CHOICES
            ):
                raise ValueError("A resolução deve ser 360p, 720p, 1080p ou melhor.")
            return

        raise ValueError("Tipo de mídia inválido.")

    @classmethod
    def for_audio(
        cls,
        audio_format: AudioFormat = AudioFormat.MP3,
        *,
        bitrate_kbps: int | None = None,
    ) -> DownloadProfile:
        if bitrate_kbps is None and audio_format not in _LOSSLESS_AUDIO_FORMATS:
            bitrate_kbps = 192
        return cls(
            media_kind=MediaKind.AUDIO,
            audio_format=audio_format,
            audio_bitrate_kbps=bitrate_kbps,
        )

    @classmethod
    def for_video(
        cls,
        video_format: VideoFormat = VideoFormat.MP4_COMPATIBLE,
        *,
        max_height: int | None = None,
    ) -> DownloadProfile:
        return cls(
            media_kind=MediaKind.VIDEO,
            video_format=video_format,
            max_video_height=max_height,
        )

    @property
    def output_extension(self) -> str | None:
        if self.media_kind is MediaKind.AUDIO:
            assert self.audio_format is not None
            return _AUDIO_OUTPUT_EXTENSIONS[self.audio_format]
        if self.video_format in {VideoFormat.MP4_COMPATIBLE, VideoFormat.MP4_FAST}:
            return "mp4"
        if self.video_format is VideoFormat.WEBM:
            return "webm"
        return None

    @property
    def supports_thumbnail(self) -> bool:
        return not (
            self.audio_format is AudioFormat.WAV
            or self.video_format is VideoFormat.ORIGINAL
        )


DEFAULT_DOWNLOAD_PROFILE = DownloadProfile.for_audio()
