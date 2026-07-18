"""
Core file-organizing logic for Smart File Organizer Pro.

FileOrganizer decides what happens to a single file: ignore it, skip
it (still downloading / locked), or move it into the correct category
folder inside Downloads - with automatic retries on transient Windows
file locks and safe duplicate-name handling.
"""

import logging
import shutil
import time
from pathlib import Path

import config
import utils


class FileOrganizer:
    """Encapsulates the logic required to safely categorize and move one file."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        utils.ensure_destination_folders_exist(self.logger)

    def handle_new_file(self, file_path: Path) -> None:
        """
        Entry point for processing a single file event.

        Runs every safety check (folders, hidden/system files, ignored
        extensions, incomplete downloads), waits for the file to finish
        being written, then moves it into its category folder.
        """
        path = Path(file_path)

        try:
            if not path.exists():
                # Common for very short-lived temp files - nothing to do.
                return

            if path.is_dir():
                # Folders are never moved or descended into manually;
                # watchdog's recursion handles traversal for us.
                return

            if utils.is_already_organized(path):
                # File already lives inside one of our own destination
                # folders (e.g. picked up again by recursive watching
                # right after we moved it there). Leave it alone.
                return

            if utils.is_hidden_or_system(path):
                self.logger.info(f"[IGNORED] Hidden/system file left in place: {path.name}")
                return

            if utils.is_incomplete_download(path):
                self.logger.info(f"[SKIPPED] Incomplete download, waiting: {path.name}")
                return

            if utils.has_ignored_suffix(path):
                self.logger.info(f"[IGNORED] Extension excluded by config: {path.name}")
                return

            if not utils.wait_until_stable(path, self.logger):
                return

            category = utils.get_category_for_file(path)
            destination_folder = config.DESTINATION_FOLDERS.get(
                category, config.DESTINATION_FOLDERS["Others"]
            )
            self._move_file(path, destination_folder)

        except FileNotFoundError:
            self.logger.warning(f"[SKIPPED] File vanished during processing: {path.name}")
        except PermissionError as exc:
            self.logger.warning(f"[RETRY] Permission denied while inspecting {path.name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - the app must never crash
            self.logger.error(f"[ERROR] Unexpected error handling {path.name}: {exc}")

    def _move_file(self, source: Path, destination_folder: Path) -> None:
        """Move a single file into destination_folder, retrying on lock errors."""
        destination_folder.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, config.MAX_MOVE_RETRY_ATTEMPTS + 1):
            if not source.exists():
                self.logger.warning(f"[SKIPPED] Source vanished before move: {source.name}")
                return

            target_path = utils.resolve_duplicate_path(destination_folder, source.name)

            try:
                shutil.move(str(source), str(target_path))
                self.logger.info(
                    f"[MOVED] {source.name} -> {target_path.parent.name}/{target_path.name}"
                )
                return
            except PermissionError as exc:
                self.logger.warning(
                    f"[RETRY] Permission denied moving {source.name} "
                    f"(attempt {attempt}/{config.MAX_MOVE_RETRY_ATTEMPTS}): {exc}"
                )
                time.sleep(config.RETRY_BACKOFF_SECONDS)
            except FileNotFoundError:
                self.logger.warning(f"[SKIPPED] File disappeared during move: {source.name}")
                return
            except FileExistsError:
                # Rare race: something else created the target between
                # resolve_duplicate_path() and shutil.move(). Retry to
                # recompute a fresh, non-colliding name.
                self.logger.warning(f"[RETRY] Target name collided, recalculating: {source.name}")
                time.sleep(config.RETRY_BACKOFF_SECONDS)
            except OSError as exc:
                self.logger.error(f"[ERROR] Unexpected OS error moving {source.name}: {exc}")
                time.sleep(config.RETRY_BACKOFF_SECONDS)

        self.logger.error(
            f"[ERROR] Giving up on {source.name} after {config.MAX_MOVE_RETRY_ATTEMPTS} attempts."
        )
