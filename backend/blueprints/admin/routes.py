# file: backend/blueprints/admin/routes.py

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
    current_app,
)
from flask_login import current_user, login_required
import os
from werkzeug.utils import secure_filename

from ...extensions import db
from ...models.user import User, UserRole
from ...models.product import Category, Product
from ...models.order import Order
from ...models.payment import Payment
from ...models.crm import Company
from ...models.b2b_check import B2BCheckResult
from . import bp
from .forms import CategoryForm, ProductForm, slugify
from .services import get_admin_dashboard_data


def save_uploaded_file(file_field, subfolder="uploads"):
    """Save uploaded file and return relative path."""
    if not file_field.data:
        return None
    filename = secure_filename(file_field.data.filename)
    upload_dir = os.path.join(current_app.root_path, "static", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file_field.data.save(file_path)
    return f"/static/{subfolder}/{filename}"


def admin_required(view_func):
    """
    Декоратор для перевірки, що користувач — адміністратор або суперадмін.
    """
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


# ---------- DASHBOARD ----------


@bp.route("/")
@admin_required
def dashboard():
    data = get_admin_dashboard_data()
    return render_template("admin/dashboard.html", **data)


# ---------- CATEGORIES CRUD ----------


@bp.route("/categories")
@admin_required
def categories_list():
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/categories_list.html", categories=categories)


@bp.route("/categories/create", methods=["GET", "POST"])
@admin_required
def category_create():
    form = CategoryForm()

    # наповнюємо список батьківських категорій
    form.parent_id.choices = [(0, "--- немає ---")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()
    ]

    if form.validate_on_submit():
        parent_id = form.parent_id.data or 0
        parent = Category.query.get(parent_id) if parent_id else None

        slug = form.slug.data or slugify(form.name.data)
        image_path = save_uploaded_file(form.image)

        category = Category(
            name=form.name.data,
            slug=slug,
            description=form.description.data or None,
            image=image_path,
            parent=parent,
        )
        db.session.add(category)
        db.session.commit()
        flash("Категорію створено.", "success")
        return redirect(url_for("admin.categories_list"))

    return render_template("admin/category_form.html", form=form, title="Створити категорію")


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def category_edit(category_id: int):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    form.parent_id.choices = [(0, "--- немає ---")] + [
        (c.id, c.name) for c in Category.query.filter(Category.id != category.id).order_by(Category.name.asc()).all()
    ]
    form.parent_id.data = category.parent_id or 0

    if form.validate_on_submit():
        parent_id = form.parent_id.data or 0
        parent = Category.query.get(parent_id) if parent_id else None

        image_path = save_uploaded_file(form.image)
        if image_path:
            category.image = image_path

        category.name = form.name.data
        category.slug = form.slug.data
        category.description = form.description.data or None
        category.parent = parent

        db.session.commit()
        flash("Категорію оновлено.", "success")
        return redirect(url_for("admin.categories_list"))

    return render_template("admin/category_form.html", form=form, title="Редагувати категорію")


@bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def category_delete(category_id: int):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Категорію видалено.", "info")
    return redirect(url_for("admin.categories_list"))


# ---------- PRODUCTS CRUD ----------


@bp.route("/products")
@admin_required
def products_list():
    products = (
        Product.query.order_by(Product.created_at.desc())
        .all()
    )
    return render_template("admin/products_list.html", products=products)


@bp.route("/products/create", methods=["GET", "POST"])
@admin_required
def product_create():
    form = ProductForm()
    form.category_id.choices = [(0, "--- без категорії ---")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()
    ]

    if form.validate_on_submit():
        category_id = form.category_id.data or 0
        category = Category.query.get(category_id) if category_id else None

        slug = form.slug.data or slugify(form.name.data)
        image_path = save_uploaded_file(form.main_image)

        product = Product(
            name=form.name.data,
            slug=slug,
            description=form.description.data or None,
            category=category,
            price_b2c=form.price_b2c.data,
            price_b2b=form.price_b2b.data,
            currency=form.currency.data,
            is_active=form.is_active.data,
            main_image_url=image_path,
        )
        db.session.add(product)
        db.session.commit()
        flash("Товар створено.", "success")
        return redirect(url_for("admin.products_list"))

    return render_template("admin/product_form.html", form=form, title="Створити товар")


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id: int):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    form.category_id.choices = [(0, "--- без категорії ---")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()
    ]
    form.category_id.data = product.category_id or 0

    if form.validate_on_submit():
        category_id = form.category_id.data or 0
        category = Category.query.get(category_id) if category_id else None

        image_path = save_uploaded_file(form.main_image)
        if image_path:
            product.main_image_url = image_path

        product.name = form.name.data
        product.slug = form.slug.data
        product.description = form.description.data or None
        product.category = category
        product.price_b2c = form.price_b2c.data
        product.price_b2b = form.price_b2b.data
        product.currency = form.currency.data
        product.is_active = form.is_active.data

        db.session.commit()
        flash("Товар оновлено.", "success")
        return redirect(url_for("admin.products_list"))

    return render_template("admin/product_form.html", form=form, title="Редагувати товар")


@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id: int):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Товар видалено.", "info")
    return redirect(url_for("admin.products_list"))


# ---------- ORDERS & PAYMENTS ----------


@bp.route("/orders")
@admin_required
def orders_list():
    orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()
    return render_template("admin/orders_list.html", orders=orders)


@bp.route("/orders/<int:order_id>")
@admin_required
def order_detail(order_id: int):
    order = Order.query.get_or_404(order_id)
    payments = Payment.query.filter_by(order_id=order.id).all()
    return render_template("admin/order_detail.html", order=order, payments=payments)


# ---------- CRM (COMPANIES & B2B CHECKS) ----------


@bp.route("/crm/companies")
@admin_required
def companies_list():
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template("admin/companies_list.html", companies=companies)


@bp.route("/crm/companies/<int:company_id>")
@admin_required
def company_detail(company_id: int):
    company = Company.query.get_or_404(company_id)
    b2b_checks = (
        B2BCheckResult.query.filter_by(user_id=company.user_id)
        .order_by(B2BCheckResult.created_at.desc())
        .all()
    )
    return render_template("admin/company_detail.html", company=company, b2b_checks=b2b_checks)


@bp.route("/crm/b2b-checks")
@admin_required
def b2b_checks_list():
    checks = (
        B2BCheckResult.query.order_by(B2BCheckResult.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/b2b_checks_list.html", checks=checks)


# ---------- USERS ----------


@bp.route("/users")
@admin_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users_list.html", users=users)


@bp.route("/users/<int:user_id>")
@admin_required
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(10).all()
    return render_template("admin/user_detail.html", user=user, orders=orders)


@bp.route("/users/<int:user_id>/change_role", methods=["POST"])
@login_required
def change_user_role(user_id: int):
    if current_user.role != UserRole.SUPERADMIN:
        abort(403)
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in [UserRole.ADMIN, UserRole.WAREHOUSE_ADMIN, UserRole.SUPERADMIN, UserRole.B2B, UserRole.B2C]:
        user.role = new_role
        db.session.commit()
        flash(f"Роль пользователя {user.email} изменена на {new_role}.", "success")
    else:
        flash("Неверная роль.", "danger")
    return redirect(url_for('admin.users'))
