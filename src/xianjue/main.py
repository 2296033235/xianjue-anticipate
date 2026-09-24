"""Application entry point."""

import sys
import traceback
import os

from .app import create_app


def main():
    try:
        # Hide the console window on Windows.
        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            # Hide the console window (GetConsoleWindow is in kernel32).
            kernel32 = ctypes.windll.kernel32
            console_window = kernel32.GetConsoleWindow()
            if console_window and user32:
                user32.ShowWindow(console_window, 0)

        app = create_app()
        code = app.run()
        return code
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
