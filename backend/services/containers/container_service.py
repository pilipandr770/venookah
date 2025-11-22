# file: backend/services/containers/container_service.py

from datetime import datetime

from ...extensions import db
from ...models.container import Container
from .msc_client import get_container_status


def get_or_create_container(number: str) -> Container:
    container = Container.query.filter_by(number=number).first()
    if container:
        return container

    container = Container(
        number=number,
        provider="msc",
        status="unknown",
        last_location=None,
        eta=None,
        route_info=None,
    )
    db.session.add(container)
    db.session.commit()
    return container


def refresh_container_status(number: str) -> Container:
    container = get_or_create_container(number)
    data = get_container_status(number)

    container.status = data.get("status")
    container.last_location = data.get("last_location")
    eta = data.get("eta")
    if isinstance(eta, datetime):
        container.eta = eta
    container.route_info = data.get("raw")
    db.session.commit()
    return container
