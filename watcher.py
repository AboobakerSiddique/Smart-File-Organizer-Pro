"""
Filesystem watching for Smart File Organizer Pro.

Wraps the `watchdog` library to monitor the Downloads folder and the
Downloads/Telegram Desktop folder simultaneously (recursively),
dispatching new-file events to a FileOrganizer instance.
"""

import logging
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

import config
from organizer import FileOrganizer


class _NewFileHandler(FileSystemEventHandler):
    """Watchdog event handler that forwards relevant file events to the organizer."""

    def __init__(self, organizer: FileOrganizer, logger: logging.Logger) -> None:
        super().__init__()
        self.organizer = organizer
        self.logger = logger

    def on_created(self, event: FileCreatedEvent) -> None:
        """Fired when a brand-new file appears (most direct downloads/copies)."""
        if event.is_directory:
            return
        self._dispatch(Path(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:
        """
        Fired when a file is renamed in place - this is how most browsers
        finish a download (e.g. 'file.crdownload' -> 'file.pdf'), so it
        must be handled the same way as on_created.
        """
        if event.is_directory:
            return
        self._dispatch(Path(event.dest_path))

    def _dispatch(self, path: Path) -> None:
        """Hand a candidate file off to the organizer, never letting it crash the watcher."""
        try:
            self.organizer.handle_new_file(path)
        except Exception as exc:  # noqa: BLE001 - top-level safety net
            self.logger.error(f"[ERROR] Unexpected exception handling {path.name}: {exc}")


class FolderWatcher:
    """Sets up and runs a watchdog Observer across every configured folder."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.organizer = FileOrganizer(logger)
        self.observer = Observer()

    def start(self) -> None:
        """Attach a watcher to every existing configured folder and start observing."""
        handler = _NewFileHandler(self.organizer, self.logger)

        watched_any = False
        for folder in config.WATCHED_FOLDERS:
            if not folder.exists():
                self.logger.warning(f"[WARNING] Watched folder does not exist, skipping: {folder}")
                continue
            self.observer.schedule(handler, str(folder), recursive=True)
            self.logger.info(f"[INFO] Watching folder: {folder}")
            watched_any = True

        if not watched_any:
            raise RuntimeError("No valid folders to watch. Check the paths in config.py.")

        self.observer.start()

    def stop(self) -> None:
        """Stop and cleanly join the observer thread."""
        self.observer.stop()
        self.observer.join()
