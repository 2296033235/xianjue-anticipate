"""Application entry point."""

import sys
import traceback

from .app import create_app


def main():
    try:
        print("[xianjue] starting...")
        app = create_app()
        print(f"[xianjue] created, tray={app.tray.isVisible()}")
        code = app.run()
        print(f"[xianjue] exited with code {code}")
        return code
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
