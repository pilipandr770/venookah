# file: backend/blueprints/shop_account/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required

from . import bp
from ...models.order import Order


@bp.route("/profile")
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("shop/profile.html", orders=orders)
