"""
Entry point for Smart File Organizer Pro.

Initializes logging, starts the folder watcher, and keeps the
application running until the user interrupts it (Ctrl+C) or an
unrecoverable error occurs. The application is designed to never crash
on expected error conditions - see organizer.py and watcher.py.
"""

import time

import config
from logger import get_logger
from watcher import FolderWatcher


def main() -> None:
    """Wire up logging and the watcher, then run forever until interrupted."""
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("[INFO] Program started - Smart File Organizer Pro")
    logger.info(f"[INFO] Downloads folder : {config.DOWNLOADS_FOLDER}")
    logger.info(f"[INFO] Telegram folder  : {config.TELEGRAM_FOLDER}")
    logger.info("=" * 60)

    watcher = FolderWatcher(logger)

    try:
        watcher.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("[INFO] Keyboard interrupt received, shutting down...")
    except Exception as exc:  # noqa: BLE001 - top-level safety net, app must never crash
        logger.error(f"[ERROR] Unexpected fatal error: {exc}")
    finally:
        watcher.stop()
        logger.info("[INFO] Program stopped.")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
