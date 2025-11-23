# file: backend/__init__.py

"""
Backend-Paket für Venookah2.

Um die Anwendung zu starten:
FLASK_APP=backend.app flask run
oder `create_app()` im WSGI verwenden.
"""

from .app import create_app  # noqa: F401
