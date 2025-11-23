# file: backend/blueprints/admin/routes.py

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
    current_app,
    jsonify,
)
from flask_login import current_user, login_required
import os
from werkzeug.utils import secure_filename

from ...extensions import db
from ...models.user import User, UserRole
from ...models.product import Category, Product
from ...models.order import Order, OrderItem, CartItem
from ...models.payment import Payment
from ...models.warehouse import WarehouseTask
from ...models.crm import Company
from ...models.b2b_check import B2BCheckResult
from ...models.alert import Alert
from . import bp
from .forms import CategoryForm, ProductForm, slugify
from .services import get_admin_dashboard_data
import requests
import json



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
    Dekorator zur Überprüfung, dass der Nutzer Administrator oder Superadmin ist.
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

    # Fülle die Liste der übergeordneten Kategorien
    form.parent_id.choices = [(0, "--- keine ---")] + [
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
        flash("Kategorie erstellt.", "success")
        return redirect(url_for("admin.categories_list"))

    return render_template("admin/category_form.html", form=form, title="Kategorie erstellen")


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def category_edit(category_id: int):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    form.parent_id.choices = [(0, "--- keine ---")] + [
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
        flash("Kategorie aktualisiert.", "success")
        return redirect(url_for("admin.categories_list"))

    return render_template("admin/category_form.html", form=form, title="Kategorie bearbeiten")


def _prompt_file_path():
    return os.path.join(current_app.root_path, 'data', 'ai_system_prompt.txt')


@bp.route('/ai/prompt', methods=['GET', 'POST'])
@admin_required
def ai_prompt():
    """View and edit the system prompt used by the public chat assistant."""
    os.makedirs(os.path.join(current_app.root_path, 'data'), exist_ok=True)
    path = _prompt_file_path()

    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        flash('Systemanweisung aktualisiert.', 'success')
        return redirect(url_for('admin.ai_prompt'))

    current_prompt = ''
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                current_prompt = f.read()
        except Exception:
            current_prompt = ''

    return render_template('admin/ai_prompt.html', prompt=current_prompt)


@bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def category_delete(category_id: int):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Kategorie gelöscht.", "info")
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


@bp.route('/debug')
@admin_required
def debug_info():
    """Admin-only debug endpoint returning recent payments, orders and warehouse tasks."""
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(15).all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(15).all()
    tasks = WarehouseTask.query.order_by(WarehouseTask.created_at.desc()).limit(15).all()

    def p_dict(p):
        return {
            'id': p.id,
            'order_id': getattr(p, 'order_id', None),
            'provider_payment_id': p.provider_payment_id,
            'provider_session_id': p.provider_session_id,
            'status': p.status,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        }

    def o_dict(o):
        return {
            'id': o.id,
            'status': o.status,
            'total_amount': float(o.total_amount) if o.total_amount is not None else None,
            'stripe_payment_intent_id': o.stripe_payment_intent_id,
            'created_at': o.created_at.isoformat() if o.created_at else None,
        }

    def t_dict(t):
        return {
            'id': t.id,
            'order_id': t.order_id,
            'status': t.status,
            'assigned_to': t.assigned_to,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        }

    return jsonify({
        'payments': [p_dict(p) for p in payments],
        'orders': [o_dict(o) for o in orders],
        'tasks': [t_dict(t) for t in tasks],
    })


@bp.route('/debug/products_files')
@admin_required
def debug_products_files():
    """Return products and check if their main_image_url files exist on disk."""
    products = Product.query.order_by(Product.id.desc()).all()
    rows = []
    for p in products:
        url = p.main_image_url or ''
        file_exists = False
        try:
            if url.startswith('/static/'):
                rel = url[len('/static/'):]
                fs_path = os.path.join(current_app.root_path, 'static', rel.replace('/', os.sep))
                file_exists = os.path.exists(fs_path)
            else:
                # external URL
                file_exists = False
        except Exception:
            file_exists = False

        rows.append({'id': p.id, 'main_image_url': url, 'file_exists': file_exists})

    return jsonify({'products': rows})


@bp.route('/debug/products_files/fix', methods=['POST'])
@admin_required
def debug_products_files_fix():
    """Attempt to fix missing product main images by searching `static/uploads` for similar filenames."""
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    try:
        files = os.listdir(uploads_dir)
    except Exception:
        files = []

    def normalize(s: str):
        import re

        return re.sub(r'[^a-z0-9]+', '', s.lower() or '')

    fixes = []
    for p in Product.query.order_by(Product.id.asc()).all():
        url = p.main_image_url or ''
        if url and url.startswith('/static/'):
            rel = url[len('/static/'):]
            fs_path = os.path.join(current_app.root_path, 'static', rel.replace('/', os.sep))
            if os.path.exists(fs_path):
                continue

        # Try to find candidate
        slug = getattr(p, 'slug', '') or ''
        name = getattr(p, 'name', '') or ''
        candidates = []
        nslug = normalize(slug)
        nname = normalize(name)
        for f in files:
            nf = normalize(f)
            if nslug and nslug in nf:
                candidates.append(f)
            elif nname and nname in nf:
                candidates.append(f)

        chosen = None
        if candidates:
            chosen = candidates[0]
        else:
            # fallback: if only one file in uploads, use it
            if len(files) == 1:
                chosen = files[0]

        if chosen:
            new_url = f"/static/uploads/{chosen}"
            p.main_image_url = new_url
            fixes.append({'product_id': p.id, 'old_url': url, 'new_url': new_url})
            db.session.add(p)

    if fixes:
        db.session.commit()

    return jsonify({'fixed': fixes, 'uploads_count': len(files)})


@bp.route("/products/create", methods=["GET", "POST"])
@admin_required
def product_create():
    form = ProductForm()
    form.category_id.choices = [(0, "--- keine Kategorie ---")] + [
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
        flash("Produkt erstellt.", "success")
        return redirect(url_for("admin.products_list"))

    return render_template("admin/product_form.html", form=form, title="Produkt erstellen")


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id: int):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    form.category_id.choices = [(0, "--- keine Kategorie ---")] + [
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
        flash("Produkt aktualisiert.", "success")
        return redirect(url_for("admin.products_list"))

    return render_template("admin/product_form.html", form=form, title="Produkt bearbeiten")


@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id: int):
    product = Product.query.get_or_404(product_id)
    # Prevent deletion if product is referenced by order items or cart items
    try:
        order_refs = OrderItem.query.filter_by(product_id=product.id).count()
    except Exception:
        order_refs = 0

    try:
        cart_refs = CartItem.query.filter_by(product_id=product.id).count()
    except Exception:
        cart_refs = 0

    if order_refs:
        flash(
            f"Produkt kann nicht gelöscht werden: es wird in {order_refs} Bestellposition(en) verwendet. Entfernen Sie zuerst die zugehörigen Bestellungen/Positionen.",
            "danger",
        )
        return redirect(url_for("admin.products_list"))

    if cart_refs:
        flash(
            f"Produkt kann nicht gelöscht werden: es ist in {cart_refs} Warenkorb/Posten vorhanden. Entfernen Sie es zuerst aus den Warenkörben.",
            "warning",
        )
        return redirect(url_for("admin.products_list"))

    try:
        db.session.delete(product)
        db.session.commit()
        flash("Produkt gelöscht.", "info")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error deleting product")
        flash(
            "Fehler beim Löschen des Produkts. Möglicherweise referenzieren Bestellungen dieses Produkt.",
            "danger",
        )

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


@bp.route('/alerts')
@admin_required
def alerts_list():
    """List recent alerts for admin review. Supports optional `type` filter via querystring."""
    import json

    # Read filters and pagination params
    alert_type = request.args.get('type')
    is_sent = request.args.get('is_sent')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
    except Exception:
        page = 1
        per_page = 25

    query = Alert.query.order_by(Alert.created_at.desc())
    if alert_type:
        query = query.filter_by(type=alert_type)
    if is_sent in ('0', '1'):
        query = query.filter_by(is_sent=(is_sent == '1'))

    # Date filters (simple ISO date support)
    from datetime import datetime
    try:
        if date_from:
            df = datetime.fromisoformat(date_from)
            query = query.filter(Alert.created_at >= df)
        if date_to:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(Alert.created_at <= dt)
    except Exception:
        # If parsing fails, ignore date filters
        pass

    # Use SQLAlchemy/Flask-SQLAlchemy pagination
    try:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        alerts_page = pagination.items
    except Exception:
        # Fallback: limit offset
        alerts_page = query.limit(per_page).offset((page - 1) * per_page).all()
        pagination = None

    processed = []
    for a in alerts_page:
        payload = a.payload
        parsed = None
        try:
            if isinstance(payload, str):
                parsed = json.loads(payload)
            else:
                parsed = payload
        except Exception:
            parsed = payload

        user_link = None
        try:
            if isinstance(parsed, dict) and parsed.get('user_id'):
                user_link = url_for('admin.user_detail', user_id=int(parsed.get('user_id')))
        except Exception:
            user_link = None

        processed.append({'alert': a, 'payload': parsed, 'user_link': user_link})

    return render_template('admin/alerts_list.html', alerts=processed, filter_type=alert_type, pagination=pagination, page=page, per_page=per_page, is_sent=is_sent, date_from=date_from, date_to=date_to)


@bp.route('/alerts/<int:alert_id>/mark-sent', methods=['POST'])
@admin_required
def alert_mark_sent(alert_id: int):
    a = Alert.query.get_or_404(alert_id)
    try:
        from datetime import datetime
        a.is_sent = True
        a.sent_at = datetime.utcnow()
        db.session.commit()
        flash('Alert als gesendet markiert.', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to mark alert as sent')
        flash('Fehler beim Markieren des Alerts.', 'danger')
    return redirect(url_for('admin.alerts_list'))


@bp.route('/alerts/<int:alert_id>/delete', methods=['POST'])
@admin_required
def alert_delete(alert_id: int):
    a = Alert.query.get_or_404(alert_id)
    try:
        db.session.delete(a)
        db.session.commit()
        flash('Alert gelöscht.', 'info')
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to delete alert')
        flash('Fehler beim Löschen des Alerts.', 'danger')
    return redirect(url_for('admin.alerts_list'))


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
    # Load recent B2B check results for this user (if any)
    try:
        b2b_checks = (
            B2BCheckResult.query.filter_by(user_id=user.id)
            .order_by(B2BCheckResult.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception:
        # In case of schema/database differences in local dev, keep page working
        current_app.logger.exception('Failed to load B2B checks for user')
        b2b_checks = []
    return render_template("admin/user_detail.html", user=user, orders=orders)


@bp.route('/users/<int:user_id>/b2b-check', methods=['POST'])
@admin_required
def user_b2b_check(user_id: int):
    """Admin action: trigger a manual B2B re-check for the given user (runs in background)."""
    user = User.query.get_or_404(user_id)
    try:
        from ...services.b2b_checks.b2b_service import run_b2b_checks_for_user
        import threading

        def _run():
            try:
                run_b2b_checks_for_user(user)
            except Exception:
                current_app.logger.exception('Manual B2B check failed')

        t = threading.Thread(target=_run, name=f'b2b-check-user-{user_id}', daemon=True)
        t.start()
        flash('B2B-Prüfung gestartet (im Hintergrund).', 'info')
    except Exception:
        current_app.logger.exception('Failed to start manual B2B check')
        flash('Fehler beim Starten der B2B-Prüfung.', 'danger')

    return redirect(url_for('admin.user_detail', user_id=user_id))


@bp.route('/users/<int:user_id>/b2b-check.json', methods=['POST'])
@admin_required
def user_b2b_check_json(user_id: int):
    """Start a background B2B check and return JSON (non-blocking).

    Client can poll the fragment endpoint to pickup new checks.
    """
    user = User.query.get_or_404(user_id)
    try:
        from ...services.b2b_checks.b2b_service import run_b2b_checks_for_user
        import threading

        def _run():
            try:
                run_b2b_checks_for_user(user)
            except Exception:
                current_app.logger.exception('Manual B2B check failed (json)')

        t = threading.Thread(target=_run, name=f'b2b-check-user-json-{user_id}', daemon=True)
        t.start()
        return jsonify({'started': True}), 202
    except Exception:
        current_app.logger.exception('Failed to start manual B2B check (json)')
        return jsonify({'started': False}), 500


@bp.route('/users/<int:user_id>/b2b-checks-fragment')
@admin_required
def user_b2b_checks_fragment(user_id: int):
    """Return rendered HTML fragment for recent B2B checks for a user."""
    try:
        checks = (
            B2BCheckResult.query.filter_by(user_id=user_id)
            .order_by(B2BCheckResult.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception:
        current_app.logger.exception('Failed to load B2B checks fragment')
        checks = []

    return render_template('admin/_b2b_checks_fragment.html', b2b_checks=checks)


@bp.route('/users/<int:user_id>/b2b-checks-status')
@admin_required
def user_b2b_checks_status(user_id: int):
    """Return the ISO timestamp of the latest B2B check for the given user, or null."""
    try:
        latest = (
            B2BCheckResult.query.filter_by(user_id=user_id)
            .order_by(B2BCheckResult.created_at.desc())
            .first()
        )
        if latest and latest.created_at:
            return jsonify({'latest': latest.created_at.isoformat()})
        return jsonify({'latest': None})
    except Exception:
        current_app.logger.exception('Failed to fetch B2B checks status')
        return jsonify({'latest': None}), 500


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
        flash(f"Rolle des Benutzers {user.email} wurde auf {new_role} geändert.", "success")
    else:
        flash("Ungültige Rolle.", "danger")
    return redirect(url_for('admin.users_list'))


@bp.route('/ensure-default-categories', methods=['POST'])
@admin_required
def ensure_default_categories():
    """Admin action: create default shop categories if they are missing.

    This is deliberately an explicit admin POST action to avoid running
    category-creation logic at import/startup time (which may fail before
    migrations are applied).
    """
    from ...models.product import Category

    created = []
    if not Category.query.filter_by(slug='coal').first():
        c = Category(name='Kohle', slug='coal')
        db.session.add(c)
        created.append('Kohle')

    if not Category.query.filter_by(slug='tobacco').first():
        c = Category(name='Tabak (Shisha)', slug='tobacco')
        db.session.add(c)
        created.append('Tabak')

    if created:
        db.session.commit()
        flash(f"Standardkategorien erstellt: {', '.join(created)}", 'success')
    else:
        flash('Standardkategorien bereits vorhanden.', 'info')

    return redirect(url_for('admin.categories_list'))
