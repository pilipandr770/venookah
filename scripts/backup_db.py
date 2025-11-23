# file: scripts/backup_db.py

"""
Ein einfacher Stub für Datenbank-Backups.
Auf Render kann später ein eigener Mechanismus konfiguriert werden.
"""

from datetime import datetime
from pathlib import Path

from backend.config import _build_sqlalchemy_uri


def main():
    uri = _build_sqlalchemy_uri()
    print("Backup für:", uri)
    # TODO: Backup-Logik für Postgres implementieren (z. B. pg_dump via subprocess)


if __name__ == "__main__":
    main()
