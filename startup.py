"""
Optional Windows Startup registration for Smart File Organizer Pro.

DISABLED BY DEFAULT. Making an application launch automatically at
login is a meaningful system change, so nothing in this module runs
just by importing it - you must flip STARTUP_REGISTRATION_ENABLED to
True and then call register_startup() (or run this file directly).

Implementation approach: writes a small .bat launcher into the current
user's Startup folder. Windows executes every file in that folder
automatically each time the user logs in.
"""

import sys
from pathlib import Path
from typing import Optional

# Master switch - must be manually changed to True to allow registration.
STARTUP_REGISTRATION_ENABLED: bool = False

STARTUP_FOLDER: Path = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
    / "Startup"
)

LAUNCHER_NAME: str = "SmartFileOrganizerPro.bat"


def _build_launcher_content(project_root: Path) -> str:
    """Build the contents of the .bat file that silently launches main.py."""
    python_exe = sys.executable
    main_script = project_root / "main.py"
    return (
        "@echo off\n"
        f'cd /d "{project_root}"\n'
        f'start "" "{python_exe}" "{main_script}"\n'
    )


def register_startup(project_root: Optional[Path] = None) -> None:
    """
    Register Smart File Organizer Pro to run at Windows login by
    placing a launcher .bat file in the current user's Startup folder.

    Does nothing unless STARTUP_REGISTRATION_ENABLED is True.
    """
    if not STARTUP_REGISTRATION_ENABLED:
        print(
            "[INFO] Startup registration is disabled. "
            "Set STARTUP_REGISTRATION_ENABLED = True in startup.py to enable it."
        )
        return

    root = project_root or Path(__file__).resolve().parent
    STARTUP_FOLDER.mkdir(parents=True, exist_ok=True)
    launcher_path = STARTUP_FOLDER / LAUNCHER_NAME

    launcher_path.write_text(_build_launcher_content(root), encoding="utf-8")
    print(f"[INFO] Startup launcher created at: {launcher_path}")


def unregister_startup() -> None:
    """Remove the startup launcher file if it exists."""
    launcher_path = STARTUP_FOLDER / LAUNCHER_NAME
    if launcher_path.exists():
        launcher_path.unlink()
        print(f"[INFO] Startup launcher removed: {launcher_path}")
    else:
        print("[INFO] No startup launcher found to remove.")


if __name__ == "__main__":
    register_startup()
