# file: backend/blueprints/warehouse/__init__.py

from flask import Blueprint

bp = Blueprint("warehouse", __name__, url_prefix='/warehouse')

from . import routes  # noqa: E402,F401