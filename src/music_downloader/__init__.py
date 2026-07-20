"""Core package for Music Downloader."""

from music_downloader.cancellation import CancellationToken, OperationCancelled
from music_downloader.csv_importer import CsvHeaderError, import_exportify_csv
from music_downloader.dependencies import detect_media_tools
from music_downloader.download_service import DownloadService
from music_downloader.list_parser import parse_semicolon_list
from music_downloader.search_service import SearchService
from music_downloader.spotify import is_spotify_playlist_url
from music_downloader.windows_paths import sanitize_windows_filename

__all__ = [
    "CancellationToken",
    "CsvHeaderError",
    "DownloadService",
    "OperationCancelled",
    "SearchService",
    "detect_media_tools",
    "import_exportify_csv",
    "is_spotify_playlist_url",
    "parse_semicolon_list",
    "sanitize_windows_filename",
]
