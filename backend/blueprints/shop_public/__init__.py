# file: backend/blueprints/shop_public/__init__.py

from flask import Blueprint

bp = Blueprint("shop_public", __name__)

from . import routes  # noqa: E402,F401
