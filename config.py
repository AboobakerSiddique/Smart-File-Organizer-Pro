"""
Configuration module for Smart File Organizer Pro.

Every configurable value lives here: watched/destination folder paths,
file-extension-to-category mapping, ignored extensions, timing/retry
behavior, and logging configuration.
"""

from pathlib import Path

# ----------------------------------------------------------------------
# Base folders
# ----------------------------------------------------------------------

DOWNLOADS_FOLDER: Path = Path.home() / "Downloads"
TELEGRAM_FOLDER: Path = DOWNLOADS_FOLDER / "Telegram Desktop"

# Every folder the watcher should monitor.
WATCHED_FOLDERS: list[Path] = [DOWNLOADS_FOLDER, TELEGRAM_FOLDER]

# ----------------------------------------------------------------------
# Destination category folders (created inside DOWNLOADS_FOLDER only,
# never anywhere else on disk).
# ----------------------------------------------------------------------

DESTINATION_FOLDERS: dict[str, Path] = {
    "Images": DOWNLOADS_FOLDER / "Images",
    "Videos": DOWNLOADS_FOLDER / "Videos",
    "Documents": DOWNLOADS_FOLDER / "Documents",
    "Music": DOWNLOADS_FOLDER / "Music",
    "PDFs": DOWNLOADS_FOLDER / "PDFs",
    "Others": DOWNLOADS_FOLDER / "Others",
}

# ----------------------------------------------------------------------
# Extension -> category mapping
# ----------------------------------------------------------------------

IMAGE_EXTENSIONS: set[str] = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif",
    ".webp", ".svg", ".tiff", ".ico", ".heic",
}

VIDEO_EXTENSIONS: set[str] = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv",
    ".flv", ".webm", ".mpeg", ".mpg", ".3gp",
}

DOCUMENT_EXTENSIONS: set[str] = {
    ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".json", ".xml", ".md", ".rtf", ".odt", ".ods", ".odp",
}

PDF_EXTENSIONS: set[str] = {".pdf"}

MUSIC_EXTENSIONS: set[str] = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"}

# Built once at import time: maps a lowercase extension straight to its
# destination category name, so lookups elsewhere are O(1).
EXTENSION_CATEGORY_MAP: dict[str, str] = {}
for _ext in IMAGE_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[_ext] = "Images"
for _ext in VIDEO_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[_ext] = "Videos"
for _ext in DOCUMENT_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[_ext] = "Documents"
for _ext in PDF_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[_ext] = "PDFs"
for _ext in MUSIC_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[_ext] = "Music"

# ----------------------------------------------------------------------
# Extensions that must be left alone completely (never moved).
# ----------------------------------------------------------------------

IGNORED_EXTENSIONS: set[str] = {
    ".exe", ".msi", ".zip", ".rar", ".7z", ".iso", ".cab", ".apk",
}

# Temporary / in-progress download extensions used by browsers. Files
# with these extensions are still being written to disk and must never
# be touched until the browser renames/removes them.
INCOMPLETE_DOWNLOAD_EXTENSIONS: set[str] = {
    ".crdownload", ".part", ".tmp", ".download",
}

# ----------------------------------------------------------------------
# Stability / retry behavior
# ----------------------------------------------------------------------

# How long to wait between size checks while confirming a file has
# finished downloading.
STABILITY_CHECK_DELAY_SECONDS: float = 1.5

# How many consecutive size checks are attempted before giving up and
# waiting for the next filesystem event instead.
STABILITY_CHECK_ATTEMPTS: int = 5

# How many times to retry an actual move operation if Windows reports
# the file as locked (PermissionError).
MAX_MOVE_RETRY_ATTEMPTS: int = 5
RETRY_BACKOFF_SECONDS: float = 1.0

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

LOG_DIR: Path = Path(__file__).resolve().parent / "logs"
LOG_FILE: Path = LOG_DIR / "organizer.log"
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ----------------------------------------------------------------------
# Hidden / system file safety (Windows file attribute flags)
# ----------------------------------------------------------------------

FILE_ATTRIBUTE_HIDDEN: int = 0x2
FILE_ATTRIBUTE_SYSTEM: int = 0x4
