# file: backend/blueprints/shop_public/routes.py

from flask import render_template, abort, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required

from . import bp
from .forms import SearchForm
from .services import get_active_products, get_product_by_slug
from ...models.product import Category, Product
from ...models.order import Cart, CartItem, Order, OrderItem, OrderStatus
from ...extensions import db
from ...services.shipping.shipping_service import create_shipment_for_order
import stripe
from ...services.prepare_shipment import prepare_shipment


def get_or_create_cart(user_id: int) -> Cart:
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


@bp.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()
    products = get_active_products()

    # Поки пошук простий — фільтрація по назві (можемо розширити пізніше)
    if form.validate_on_submit() and form.query.data:
        q = form.query.data.lower()
        products = [p for p in products if q in p.name.lower()]

    # Розділяємо продукти на табак та вугілля за категоріями
    tobacco_products = []
    coal_products = []
    for p in products:
        if p.category and ('табак' in p.category.name.lower() or 'tobacco' in p.category.name.lower()):
            tobacco_products.append(p)
        elif p.category and ('вугілля' in p.category.name.lower() or 'coal' in p.category.name.lower() or 'уголь' in p.category.name.lower()):
            coal_products.append(p)

    return render_template("shop/index.html", form=form, products=products, tobacco_products=tobacco_products, coal_products=coal_products)


@bp.route("/product/<slug>")
def product_detail(slug: str):
    product = get_product_by_slug(slug)
    if not product:
        abort(404)

    return render_template("shop/product_detail.html", product=product)


@bp.route("/add-to-cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id: int):
    product = get_product_by_slug(request.form.get('slug')) or db.session.get(Product, product_id)
    if not product or not product.is_active:
        abort(404)

    cart = get_or_create_cart(current_user.id)
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash(f"Товар '{product.name}' додано до корзини.", "success")
    return redirect(request.referrer or url_for('shop_public.index'))


@bp.route("/cart")
@login_required
def view_cart():
    cart = get_or_create_cart(current_user.id)
    items = cart.items
    total = sum(item.quantity * (item.product.price_b2b if current_user.is_b2b else item.product.price_b2c) for item in items)
    return render_template("shop/cart.html", cart=cart, items=items, total=total)


@bp.route("/update-cart/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id: int):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.cart.user_id != current_user.id:
        abort(403)

    quantity = int(request.form.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        db.session.commit()
        flash("Кількість оновлено.", "success")
    else:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Товар видалено з корзини.", "info")
    return redirect(url_for('shop_public.view_cart'))


@bp.route("/remove-from-cart/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id: int):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.cart.user_id != current_user.id:
        abort(403)

    db.session.delete(cart_item)
    db.session.commit()
    flash("Товар видалено з корзини.", "info")
    return redirect(url_for('shop_public.view_cart'))


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = get_or_create_cart(current_user.id)
    items = cart.items
    if not items:
        flash("Корзина порожня.", "warning")
        return redirect(url_for('shop_public.view_cart'))

    total = sum(item.quantity * (item.product.price_b2b if current_user.is_b2b else item.product.price_b2c) for item in items)
    total_cents = int(total * 100)  # Stripe работает с центами

    if request.method == "POST":
        address = request.form.get('address')
        if not address:
            flash("Адреса доставки обов'язкова.", "danger")
            return redirect(url_for('shop_public.checkout'))

        # Создать заказ без коммита
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            currency=items[0].product.currency,
            is_b2b=current_user.is_b2b,
            shipping_address={"address": address},
            status=OrderStatus.NEW
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            price = item.product.price_b2b if current_user.is_b2b else item.product.price_b2c
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=price,
                currency=item.product.currency
            )
            db.session.add(order_item)

        # Очистить корзину
        CartItem.query.filter_by(cart_id=cart.id).delete()

        # Создать payment intent
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        intent = stripe.PaymentIntent.create(
            amount=total_cents,
            currency=order.currency.lower(),
            metadata={'order_id': order.id}
        )

        order.stripe_payment_intent_id = intent.id

        # Создать запись платежа
        payment = Payment(
            order_id=order.id,
            provider="stripe",
            provider_payment_id=intent.id,
            amount=total,
            currency=order.currency,
            status="pending",
        )
        db.session.add(payment)

        db.session.commit()

        return render_template("shop/checkout.html", items=items, total=total, client_secret=intent.client_secret, publishable_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

    return render_template("shop/checkout.html", items=items, total=total)


@bp.route("/test_webhook/<int:order_id>")
@login_required
def test_webhook(order_id):
    from ...services.prepare_shipment import prepare_shipment
    prepare_shipment(order_id)
    flash("Webhook simulated", "info")
    return redirect(url_for('shop_public.profile'))

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata']['order_id']

        order = Order.query.get(order_id)
        if order:
            order.status = OrderStatus.PAID
            db.session.commit()
            # Запустить подготовку shipment
            prepare_shipment(order.id)

    return '', 200
