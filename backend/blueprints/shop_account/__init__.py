# file: backend/blueprints/shop_account/__init__.py

from flask import Blueprint

bp = Blueprint("shop_account", __name__)

from . import routes  # noqa: E402,F401
