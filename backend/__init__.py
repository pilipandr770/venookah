# file: backend/__init__.py

"""
Пакет backend для Venookah2.

Щоб запустити додаток:
FLASK_APP=backend.app flask run
або використовувати create_app() в WSGI.
"""

from .app import create_app  # noqa: F401
