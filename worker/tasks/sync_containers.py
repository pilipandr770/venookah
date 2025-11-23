# file: worker/tasks/sync_containers.py

"""
Aktualisierung der Status von Seecontainern.
"""

from backend.extensions import db
from backend.models.container import Container
from backend.services.containers.container_service import refresh_container_status


def run():
    containers = Container.query.all()
    for c in containers:
        refresh_container_status(c.number)
    db.session.remove()
