# file: scripts/backup_db.py

"""
Проста заглушка для резервного копіювання БД.
На Render можна буде налаштувати свій механізм.
"""

from datetime import datetime
from pathlib import Path

from backend.config import _build_sqlalchemy_uri


def main():
    uri = _build_sqlalchemy_uri()
    print("Резервне копіювання для:", uri)
    # TODO: реалізувати логіку backup для Postgres (pg_dump через subprocess)


if __name__ == "__main__":
    main()
