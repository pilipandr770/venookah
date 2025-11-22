# file: backend/blueprints/warehouse/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required

from . import bp
from ...extensions import db
from ...models.user import UserRole
from ...models.warehouse import WarehouseTask, WarehouseTaskStatus, WarehouseCategory, WarehouseProduct
from ...models.inventory import StockItem
from ...models.order import Order, OrderStatus
from ...services.shipping.shipping_service import create_shipment_for_order
from flask import current_app, jsonify
from flask import url_for, flash


def warehouse_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in (UserRole.SUPERADMIN, UserRole.WAREHOUSE_ADMIN):
            return render_template("warehouse/access_denied.html"), 403
        return view_func(*args, **kwargs)

    return wrapped


@bp.route("/")
@warehouse_required
def dashboard():
    tasks = WarehouseTask.query.order_by(WarehouseTask.created_at.desc()).limit(50).all()
    low_stock = WarehouseProduct.query.filter(WarehouseProduct.quantity <= 10).all()
    return render_template("warehouse/dashboard.html", tasks=tasks, low_stock=low_stock)


@bp.route("/tasks")
@warehouse_required
def tasks():
    tasks = WarehouseTask.query.order_by(WarehouseTask.created_at.desc()).all()
    return render_template("warehouse/tasks.html", tasks=tasks)


@bp.route("/tasks/debug")
def tasks_debug():
    """Temporary debug endpoint: returns tasks as JSON.

    Visible if user is logged in with warehouse/admin role OR if a valid token is provided
    via query parameter `token` matching `ADMIN_DEBUG_TOKEN` in config.
    """
    token = request.args.get('token')
    allowed = False
    if current_user.is_authenticated and current_user.role in (UserRole.SUPERADMIN, UserRole.WAREHOUSE_ADMIN):
        allowed = True
    elif token and token == current_app.config.get('ADMIN_DEBUG_TOKEN'):
        allowed = True

    if not allowed:
        return jsonify({'error': 'forbidden'}), 403

    tasks = WarehouseTask.query.order_by(WarehouseTask.created_at.desc()).all()
    def t_dict(t):
        return {
            'id': t.id,
            'order_id': t.order_id,
            'status': t.status,
            'assigned_to': t.assigned_to,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        }
    return jsonify([t_dict(t) for t in tasks])


@bp.route('/orders')
@warehouse_required
def orders():
    # Show recent orders relevant for warehouse (paid or processing)
    orders = Order.query.filter(Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING])).order_by(Order.created_at.desc()).limit(100).all()
    return render_template('warehouse/orders.html', orders=orders)


@bp.route('/orders/<int:order_id>/create_task', methods=['POST'])
@warehouse_required
def create_task_from_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Only create for paid or processing orders
    if order.status not in (OrderStatus.PAID, OrderStatus.PROCESSING):
        flash('Task can be created only for paid or processing orders.', 'warning')
        return redirect(url_for('warehouse.orders'))

    existing = WarehouseTask.query.filter_by(order_id=order.id).first()
    if existing:
        flash('Task already exists for this order.', 'info')
        return redirect(url_for('warehouse.orders'))

    task = WarehouseTask(order_id=order.id, status=WarehouseTaskStatus.PENDING)
    db.session.add(task)
    db.session.commit()
    flash('Warehouse task created.', 'success')
    return redirect(url_for('warehouse.tasks'))


@bp.route('/orders/import_tasks', methods=['POST'])
@warehouse_required
def import_tasks_from_orders():
    # Create tasks for all paid orders that don't yet have a warehouse task
    candidates = Order.query.filter(Order.status == OrderStatus.PAID).all()
    created = 0
    for o in candidates:
        if not WarehouseTask.query.filter_by(order_id=o.id).first():
            t = WarehouseTask(order_id=o.id, status=WarehouseTaskStatus.PENDING)
            db.session.add(t)
            created += 1

    if created > 0:
        db.session.commit()
        flash(f'Created {created} warehouse tasks.', 'success')
    else:
        flash('No new tasks were created.', 'info')
    return redirect(url_for('warehouse.tasks'))


@bp.route("/task/<int:task_id>/start_assembling", methods=["POST"])
@warehouse_required
def start_assembling(task_id):
    task = WarehouseTask.query.get_or_404(task_id)
    task.status = WarehouseTaskStatus.ASSEMBLING
    task.assigned_to = current_user.id
    # Обновить shipment статус
    if task.order.shipments:
        for shipment in task.order.shipments:
            shipment.status = "assembling"
    db.session.commit()
    flash("Сборка начата.", "success")
    return redirect(url_for('warehouse.tasks'))


@bp.route("/task/<int:task_id>/pack", methods=["POST"])
@warehouse_required
def pack_task(task_id):
    task = WarehouseTask.query.get_or_404(task_id)
    task.status = WarehouseTaskStatus.PACKING
    # Обновить shipment статус
    if task.order.shipments:
        for shipment in task.order.shipments:
            shipment.status = "packing"
    db.session.commit()
    flash("Упаковка начата.", "success")
    return redirect(url_for('warehouse.tasks'))


@bp.route("/task/<int:task_id>/ship", methods=["POST"])
@warehouse_required
def ship_task(task_id):
    task = WarehouseTask.query.get_or_404(task_id)
    task.status = WarehouseTaskStatus.SHIPPED
    task.order.status = OrderStatus.SHIPPED
    # Обновить shipment статус
    if task.order.shipments:
        for shipment in task.order.shipments:
            shipment.status = "shipped"
    db.session.commit()
    flash("Отправлено.", "success")
    return redirect(url_for('warehouse.tasks'))


@bp.route("/inventory")
@warehouse_required
def inventory():
    stocks = WarehouseProduct.query.all()
    return render_template("warehouse/inventory.html", stocks=stocks)


@bp.route("/products")
@warehouse_required
def products():
    products = WarehouseProduct.query.all()
    return render_template("warehouse/products.html", products=products)


@bp.route("/products/create", methods=["GET", "POST"])
@warehouse_required
def create_product():
    if request.method == "POST":
        sku = request.form.get('sku')
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        quantity = int(request.form.get('quantity', 0))
        location = request.form.get('location')

        product = WarehouseProduct(
            sku=sku,
            name=name,
            description=description,
            category_id=category_id if category_id else None,
            quantity=quantity,
            location=location
        )
        db.session.add(product)
        db.session.commit()
        flash("Товар создан.", "success")
        return redirect(url_for('warehouse.products'))
    
    categories = WarehouseCategory.query.all()
    return render_template("warehouse/create_product.html", categories=categories)


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@warehouse_required
def edit_product(product_id):
    product = WarehouseProduct.query.get_or_404(product_id)
    if request.method == "POST":
        product.sku = request.form.get('sku')
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category_id = request.form.get('category_id') or None
        product.quantity = int(request.form.get('quantity', 0))
        product.location = request.form.get('location')
        db.session.commit()
        flash("Товар обновлен.", "success")
        return redirect(url_for('warehouse.products'))
    
    categories = WarehouseCategory.query.all()
    return render_template("warehouse/edit_product.html", product=product, categories=categories)


@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@warehouse_required
def delete_product(product_id):
    product = WarehouseProduct.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Товар удален.", "success")
    return redirect(url_for('warehouse.products'))


@bp.route("/categories")
@warehouse_required
def categories():
    categories = WarehouseCategory.query.all()
    return render_template("warehouse/categories.html", categories=categories)


@bp.route("/categories/create", methods=["GET", "POST"])
@warehouse_required
def create_category():
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')

        category = WarehouseCategory(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash("Категория создана.", "success")
        return redirect(url_for('warehouse.categories'))
    
    return render_template("warehouse/create_category.html")


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@warehouse_required
def edit_category(category_id):
    category = WarehouseCategory.query.get_or_404(category_id)
    if request.method == "POST":
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        db.session.commit()
        flash("Категория обновлена.", "success")
        return redirect(url_for('warehouse.categories'))
    
    return render_template("warehouse/edit_category.html", category=category)


@bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@warehouse_required
def delete_category(category_id):
    category = WarehouseCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Категория удалена.", "success")
    return redirect(url_for('warehouse.categories'))