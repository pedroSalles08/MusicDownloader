from music_downloader.dependencies import detect_media_tools


def test_detects_both_tools_with_injected_resolver() -> None:
    paths = {
        "ffmpeg": r"C:\tools\ffmpeg.exe",
        "ffprobe": r"C:\tools\ffprobe.exe",
    }
    requested: list[str] = []

    def resolver(name: str) -> str | None:
        requested.append(name)
        return paths.get(name)

    result = detect_media_tools(resolver)

    assert requested == ["ffmpeg", "ffprobe"]
    assert result.available
    assert result.missing == ()
    assert result.ffmpeg.path == paths["ffmpeg"]
    assert result.ffprobe.path == paths["ffprobe"]
    assert result.guidance == "FFmpeg e FFprobe encontrados."


def test_reports_each_missing_tool_with_actionable_guidance() -> None:
    result = detect_media_tools(
        lambda name: r"C:\tools\ffmpeg.exe" if name == "ffmpeg" else None
    )

    assert not result.available
    assert result.missing == ("ffprobe",)
    assert "ffprobe" in result.guidance
    assert "PATH" in result.guidance
    assert "Instale o FFmpeg" in result.guidance


def test_reports_both_missing_tools() -> None:
    result = detect_media_tools(lambda _name: None)

    assert result.missing == ("ffmpeg", "ffprobe")
    assert "ffmpeg e ffprobe" in result.guidance
