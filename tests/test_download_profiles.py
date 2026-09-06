from __future__ import annotations

import pytest

from music_downloader.download_profiles import (
    DEFAULT_DOWNLOAD_PROFILE,
    AUDIO_BITRATE_CHOICES,
    VIDEO_HEIGHT_CHOICES,
    AudioFormat,
    DownloadProfile,
    MediaKind,
    VideoFormat,
)


def test_default_profile_preserves_mp3_192_behavior() -> None:
    assert DEFAULT_DOWNLOAD_PROFILE == DownloadProfile.for_audio()
    assert DEFAULT_DOWNLOAD_PROFILE.media_kind is MediaKind.AUDIO
    assert DEFAULT_DOWNLOAD_PROFILE.audio_format is AudioFormat.MP3
    assert DEFAULT_DOWNLOAD_PROFILE.audio_bitrate_kbps == 192
    assert DEFAULT_DOWNLOAD_PROFILE.output_extension == "mp3"


@pytest.mark.parametrize(
    ("audio_format", "extension"),
    [
        (AudioFormat.AAC, "m4a"),
        (AudioFormat.ALAC, "m4a"),
        (AudioFormat.FLAC, "flac"),
        (AudioFormat.M4A, "m4a"),
        (AudioFormat.MP3, "mp3"),
        (AudioFormat.OPUS, "opus"),
        (AudioFormat.VORBIS, "ogg"),
        (AudioFormat.WAV, "wav"),
    ],
)
def test_audio_profiles_expose_the_real_final_extension(
    audio_format: AudioFormat, extension: str
) -> None:
    profile = DownloadProfile.for_audio(audio_format)

    assert profile.output_extension == extension
    assert profile.audio_bitrate_kbps == (
        None if audio_format in {AudioFormat.ALAC, AudioFormat.FLAC, AudioFormat.WAV} else 192
    )


@pytest.mark.parametrize("bitrate", AUDIO_BITRATE_CHOICES)
def test_supported_audio_bitrates_are_valid(bitrate: int) -> None:
    assert DownloadProfile.for_audio(
        AudioFormat.MP3, bitrate_kbps=bitrate
    ).audio_bitrate_kbps == bitrate


def test_lossless_audio_rejects_a_misleading_bitrate() -> None:
    with pytest.raises(ValueError, match="sem perdas"):
        DownloadProfile(
            media_kind=MediaKind.AUDIO,
            audio_format=AudioFormat.FLAC,
            audio_bitrate_kbps=320,
        )


@pytest.mark.parametrize("height", (*VIDEO_HEIGHT_CHOICES, None))
def test_video_profiles_accept_supported_resolution_limits(height: int | None) -> None:
    profile = DownloadProfile.for_video(VideoFormat.MP4_FAST, max_height=height)

    assert profile.max_video_height == height
    assert profile.output_extension == "mp4"


def test_original_video_has_dynamic_extension_and_no_thumbnail_guarantee() -> None:
    profile = DownloadProfile.for_video(VideoFormat.ORIGINAL)

    assert profile.output_extension is None
    assert not profile.supports_thumbnail


def test_invalid_cross_media_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="somente video_format"):
        DownloadProfile(
            media_kind=MediaKind.VIDEO,
            audio_format=AudioFormat.MP3,
            video_format=VideoFormat.WEBM,
        )
