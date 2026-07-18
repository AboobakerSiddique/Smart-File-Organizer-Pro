"""
Utility helpers shared across Smart File Organizer Pro.

Includes download-completion detection, duplicate-name resolution
(matching Windows Explorer's "name (1).ext" convention), hidden/system
file detection, and destination-folder bootstrapping.
"""

import logging
import time
from pathlib import Path
from typing import Optional

import config


def has_ignored_suffix(path: Path) -> bool:
    """Return True if the file has an extension that must never be moved."""
    return path.suffix.lower() in config.IGNORED_EXTENSIONS


def is_incomplete_download(path: Path) -> bool:
    """Return True if the file looks like an in-progress browser download."""
    return path.suffix.lower() in config.INCOMPLETE_DOWNLOAD_EXTENSIONS


def is_already_organized(path: Path) -> bool:
    """Return True if the file already lives directly inside a destination category folder."""
    return path.parent in config.DESTINATION_FOLDERS.values()


def is_hidden_or_system(path: Path) -> bool:
    """
    Return True if the given path is a hidden or system file/folder on
    Windows, or a dotfile-style hidden file on other platforms.
    """
    if path.name.startswith("."):
        return True

    try:
        attrs = path.stat().st_file_attributes  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        # st_file_attributes only exists on Windows; other platforms
        # already handled above via the dotfile check.
        return False

    return bool(attrs & (config.FILE_ATTRIBUTE_HIDDEN | config.FILE_ATTRIBUTE_SYSTEM))


def get_category_for_file(path: Path) -> str:
    """
    Determine the destination category name for a file based on its
    extension, falling back to 'Others' for unrecognized types.
    """
    return config.EXTENSION_CATEGORY_MAP.get(path.suffix.lower(), "Others")


def wait_until_stable(path: Path, logger: logging.Logger) -> bool:
    """
    Poll a file's size until it stops changing between successive
    checks, indicating that whatever process is writing to it (a
    download, a copy, etc.) has finished.

    Returns True once the file is confirmed stable, False if the file
    disappeared or never stabilized within the configured attempt
    budget (in which case it will simply be picked up again on the
    next filesystem event).
    """
    previous_size: Optional[int] = None

    for attempt in range(1, config.STABILITY_CHECK_ATTEMPTS + 1):
        if not path.exists():
            logger.warning(f"[SKIPPED] File disappeared before it stabilized: {path.name}")
            return False

        try:
            current_size = path.stat().st_size
        except OSError as exc:
            logger.warning(f"[RETRY] Could not read size of {path.name} (attempt {attempt}): {exc}")
            time.sleep(config.STABILITY_CHECK_DELAY_SECONDS)
            continue

        if previous_size is not None and current_size == previous_size:
            return True

        previous_size = current_size
        time.sleep(config.STABILITY_CHECK_DELAY_SECONDS)

    logger.warning(f"[SKIPPED] File never stabilized, will retry on next event: {path.name}")
    return False


def resolve_duplicate_path(destination_folder: Path, filename: str) -> Path:
    """
    Return a non-colliding destination path inside destination_folder,
    following Windows Explorer's 'name (1).ext', 'name (2).ext', ...
    convention. The original file is never overwritten.
    """
    target = destination_folder / filename
    if not target.exists():
        return target

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1

    while True:
        candidate = destination_folder / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def ensure_destination_folders_exist(logger: logging.Logger) -> None:
    """Create every category destination folder inside Downloads if it's missing."""
    for name, folder_path in config.DESTINATION_FOLDERS.items():
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error(f"[ERROR] Could not create destination folder '{name}': {exc}")
