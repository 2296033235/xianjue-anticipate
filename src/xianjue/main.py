"""Application entry point."""

from .app import create_app


def main():
    app = create_app()
    return app.run()

