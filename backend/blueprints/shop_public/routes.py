# file: backend/blueprints/shop_public/routes.py

from flask import render_template, abort, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required

from . import bp
from .forms import SearchForm
from .services import get_active_products, get_product_by_slug
from ...models.product import Category, Product
from ...models.order import Cart, CartItem, Order, OrderItem, OrderStatus
from ...models.payment import Payment
from ...extensions import db
from ...services.shipping.shipping_service import create_shipment_for_order
import stripe
import os
import requests
from ...services.prepare_shipment import prepare_shipment
from ...ai.whisper_client import transcribe_audio, get_openai_key
from ...models.warehouse import WarehouseProduct, WarehouseTask
from ...models.shipping import Shipment
from ...models.order import Order, OrderItem
from ...models.product import Product
from io import BytesIO
import io
import csv
import textwrap


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

    # Suche vorerst einfach — Filterung nach Name (kann später erweitert werden)
    if form.validate_on_submit() and form.query.data:
        q = form.query.data.lower()
        products = [p for p in products if q in p.name.lower()]

    # Produkte nach Kategorie in Tabak und Kohle aufteilen
    tobacco_products = []
    coal_products = []
    for p in products:
        if p.category and (
            'табак' in p.category.name.lower()
            or 'tobacco' in p.category.name.lower()
            or 'tabak' in p.category.name.lower()
        ):
            tobacco_products.append(p)
        elif p.category and (
            'вугілля' in p.category.name.lower()
            or 'coal' in p.category.name.lower()
            or 'уголь' in p.category.name.lower()
            or 'kohle' in p.category.name.lower()
        ):
            coal_products.append(p)

    return render_template("shop/index.html", form=form, products=products, tobacco_products=tobacco_products, coal_products=coal_products)


@bp.route("/product/<slug>")
def product_detail(slug: str):
    product = get_product_by_slug(slug)
    if not product:
        abort(404)

    return render_template("shop/product_detail.html", product=product)


@bp.route('/privacy')
def privacy_policy():
    return render_template('pages/privacy.html')


@bp.route('/terms')
def terms_and_conditions():
    return render_template('pages/terms.html')


@bp.route('/impressum')
def impressum():
    return render_template('pages/impressum.html')


@bp.route('/contact')
def contact():
    return render_template('pages/contact.html')


@bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Simple chat endpoint that forwards user message to OpenAI Chat Completions API.

    Expects JSON: {"message": "..."}
    Returns JSON: {"reply": "..."}
    """
    data = request.get_json(force=True) or {}
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    # Load system prompt from file (editable by admin)
    prompt_path = os.path.join(current_app.root_path, 'data', 'ai_system_prompt.txt')
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read() or ''
        except Exception:
            system_prompt = ''
    else:
        system_prompt = ''

    # Resolve OpenAI key using the same logic as STT helper (env or .env)
    openai_key = get_openai_key()
    model = current_app.config.get('OPENAI_MODEL') or os.getenv('OPENAI_MODEL') or 'gpt-4o-mini'

    if not openai_key:
        # fall back to internal mock if key not configured
        return jsonify({'reply': f'[AI mock] {user_message} (no OPENAI_API_KEY)'}), 200

    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {openai_key}',
        'Content-Type': 'application/json'
    }

    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': user_message})

    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.2,
        'max_tokens': 800,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        j = resp.json()
        reply = ''
        # OpenAI response shape: choices[0].message.content
        if 'choices' in j and len(j['choices']) > 0:
            reply = j['choices'][0].get('message', {}).get('content', '')
        else:
            reply = j.get('error', {}).get('message', 'No reply')

        return jsonify({'reply': reply})
    except requests.RequestException as e:
        current_app.logger.exception('OpenAI request failed')
        return jsonify({'error': 'OpenAI request failed', 'detail': str(e)}), 500


@bp.route('/api/ai/owner_query', methods=['POST'])
def owner_query():
    """Endpoint for owner queries from Telegram bot.

    Accepts multipart/form-data with either 'audio' file or 'message' text and a 'department' field.
    Returns JSON {'reply': '...'}.
    """
    # Accept department from form, querystring, or default to 'shop'
    department = (request.form.get('department') or request.args.get('department') or request.values.get('department'))
    if not department:
        department = 'shop'

    # Debug logging to diagnose 400s: log what fields were received
    try:
        body_preview = (request.get_data(as_text=True) or '')[:1000]
    except Exception:
        body_preview = '<unreadable body>'
    # Use formatted log line so it appears in simple logs
    current_app.logger.info(
        f"owner_query incoming request: department={department} form={dict(request.form)} files={list(request.files.keys())} args={dict(request.args)} body_preview={body_preview}"
    )
    if not department:
        return jsonify({'error': 'department required'}), 400

    # Determine user message: audio file or text
    user_message = None
    if 'audio' in request.files:
        f = request.files['audio']
        try:
            # transcribe_audio returns either a string or dict {'text','language'}
            tr = transcribe_audio(f)
        except Exception:
            current_app.logger.exception('Transcription failed')
            return jsonify({'error': 'transcription failed'}), 500

        # Safely log transcription result; avoid letting logging formatting
        # errors interrupt normal flow.
        try:
            current_app.logger.info(f"transcription result: {tr}")
        except Exception:
            current_app.logger.debug('transcription result logging failed', exc_info=True)

        # Normalize transcription to user_message + detected_language
        if isinstance(tr, dict):
            user_message = tr.get('text', '')
            detected_language = tr.get('language')
        else:
            user_message = tr or ''
            detected_language = None
        # log audio file size
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            current_app.logger.info(f"received audio file, size={size} bytes")
        except Exception:
            pass
        # If transcription returned the mock placeholder or empty text, inform the user
        if not user_message or not str(user_message).strip() or str(user_message).strip() == '[Mock transcription]':
            current_app.logger.warning('Transcription returned empty or mock text')
            return jsonify({
                'error': 'transcription not available',
                'detail': 'Speech-to-text is not configured or returned no text. Please send a text question or set OPENAI_API_KEY for transcription.'
            }), 400
    else:
        # Accept message from form, querystring, JSON, or 'text' key
        user_message = None
        if request.values:
            user_message = request.values.get('message') or request.values.get('text')
        if not user_message:
            json_body = request.get_json(silent=True) or {}
            if isinstance(json_body, dict):
                user_message = json_body.get('message') or json_body.get('text')

    # Avoid complex f-strings in logger; compose the message separately to
    # prevent unexpected evaluation errors (slicing or format issues).
    try:
        preview = (user_message or '')[:120]
    except Exception:
        preview = '<unpreviewable>'
    current_app.logger.debug("owner_query received: department=%s has_audio=%s message_preview=%s",
                             department, 'audio' in request.files, preview)

    if not user_message:
        return jsonify({'error': 'empty message', 'detail': 'no message provided in form/text/json or audio provided'}), 400

    # Load system prompt
    prompt_path = os.path.join(current_app.root_path, 'data', 'ai_system_prompt.txt')
    system_prompt = ''
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, 'r', encoding='utf-8') as fh:
                system_prompt = fh.read() or ''
        except Exception:
            system_prompt = ''

    # Build a small DB snapshot depending on department and also produce a CSV
    snapshot_lines = []
    csv_snap = None
    # Per-department schema (hard-coded in code). These describe column meanings
    # and are authoritative: they will be sent to the model as part of system context.
    department_schemas = {
        'warehouse': [
            ('sku', 'Stock keeping unit identifier'),
            ('name', 'Product name'),
            ('quantity', 'Current on-hand quantity (integer)'),
            ('location', 'Warehouse location code')
        ],
        'shop': [
            ('category', 'Category or group name'),
            ('product', 'Product name'),
            ('price', 'Unit price (numeric, local currency)'),
            ('sold', 'Quantity sold in the snapshot period'),
            ('revenue', 'Revenue generated for that row (currency)')
        ],
        'sea': [
            ('order_id', 'Internal order id'),
            ('provider', 'Shipping provider name'),
            ('tracking_number', 'Carrier tracking number'),
            ('eta', 'Estimated arrival date (YYYY-MM-DD)')
        ]
    }

    # Prepare a human-readable schema explanation for the selected department
    schema_explanation = ''
    try:
        key = department.lower()
        if key in department_schemas:
            cols = department_schemas[key]
            lines = [f"- `{c}`: {desc}" for c, desc in cols]
            schema_explanation = 'This snapshot has the following columns:\n' + '\n'.join(lines)
        else:
            schema_explanation = 'No fixed schema is defined for this department.'
    except Exception:
        schema_explanation = ''
    try:
        if department.lower() in ('warehouse', 'склад', 'склад'):
            # Provide a broader inventory snapshot for warehouse: include up to 200 products,
            # ordered by quantity descending so the model sees both high-stock and low-stock items.
            products = WarehouseProduct.query.order_by(WarehouseProduct.quantity.desc()).limit(200).all()
            pending = WarehouseTask.query.filter(WarehouseTask.status == 'pending').count()
            total_items = len(products)
            total_quantity = sum([int(p.quantity or 0) for p in products])
            low = [p for p in products if (p.quantity or 0) <= 10]
            snapshot_lines.append(f'Inventory snapshot: items_returned={total_items} total_quantity={total_quantity}')
            snapshot_lines.append(f'Low stock items (<=10) in snapshot: {len(low)}')
            snapshot_lines.append(f'Pending warehouse tasks: {pending}')
            for p in (low[:20]):
                snapshot_lines.append(f'- {p.sku} {p.name}: qty={p.quantity}, location={p.location}')

            # CSV snapshot (sku,name,quantity,location) include the full returned set (capped)
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['sku', 'name', 'quantity', 'location'])
            for p in products:
                writer.writerow([p.sku, p.name, p.quantity, p.location])
            csv_snap = out.getvalue()

        elif department.lower() in ('shop', 'магазин'):
            recent_orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
            total_recent = sum([float(o.total_amount or 0) for o in recent_orders])
            snapshot_lines.append(f'Recent orders (last {len(recent_orders)}): total_amount_sum={total_recent}')
            # top products by quantity in recent orders
            items = (
                OrderItem.query.join(Product, OrderItem.product_id == Product.id)
                .order_by(OrderItem.quantity.desc()).limit(50).all()
            )
            for it in items:
                snapshot_lines.append(f'- {it.product.name} x{it.quantity}')

            # CSV snapshot (product_name,quantity)
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['product_name', 'quantity'])
            for it in items:
                writer.writerow([it.product.name, it.quantity])
            csv_snap = out.getvalue()

        elif department.lower() in ('sea', 'морские', 'морские доставки', 'доставка морских грузов'):
            upcoming = Shipment.query.filter(Shipment.eta != None).order_by(Shipment.eta.asc()).limit(50).all()
            snapshot_lines.append(f'Upcoming shipments: {len(upcoming)}')
            for s in upcoming:
                eta = s.eta.strftime('%Y-%m-%d') if s.eta else 'n/a'
                snapshot_lines.append(f'- Order {s.order_id} provider={s.provider} tracking={s.tracking_number} ETA={eta}')

            # CSV snapshot (order_id,provider,tracking_number,eta)
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['order_id', 'provider', 'tracking_number', 'eta'])
            for s in upcoming:
                eta = s.eta.strftime('%Y-%m-%d') if s.eta else ''
                writer.writerow([s.order_id, s.provider, s.tracking_number, eta])
            csv_snap = out.getvalue()
        else:
            snapshot_lines.append('No department-specific snapshot available.')
    except Exception:
        current_app.logger.exception('Error building snapshot')
        snapshot_lines.append('Error building snapshot (internal)')

    # Compose messages for OpenAI
    messages = []
    # Load department-specific instruction file if present
    instructions = ''
    try:
        instr_path = os.path.join(current_app.root_path, 'data', f'ai_instructions_{department.lower()}.txt')
        if os.path.exists(instr_path):
            with open(instr_path, 'r', encoding='utf-8') as ih:
                instructions = ih.read() or ''
    except Exception:
        instructions = ''

    # Combine generic system prompt and department instructions
    if system_prompt:
        combined = system_prompt
        if instructions:
            combined = instructions + "\n\n" + combined
        messages.append({'role': 'system', 'content': combined})
    else:
        if instructions:
            messages.append({'role': 'system', 'content': instructions})

    # Add authoritative schema as internal context. The assistant MUST NOT explain the schema
    # to the owner; it should use the schema internally to interpret the CSV and answer
    # concisely and directly.
    if schema_explanation:
        schema_internal = textwrap.dedent(f"""
            [INTERNAL] Department data schema (do NOT explain to owner):
            {schema_explanation}

            Behavior rules (apply strictly):
            - Use the schema internally to interpret the CSV snapshot and rows; do NOT explain the schema to the owner.
            - Answer concisely and directly based only on the provided data. Do not invent numbers.
            - If the data is incomplete or truncated, state that briefly and include a confidence note.
            - Always answer in the same language as the question.
        """)
        messages.append({'role': 'system', 'content': schema_internal})

    # include CSV snapshot as a system message with explanation (cap length)
    if csv_snap:
        max_len = 16000
        csv_text = csv_snap[:max_len]
        if len(csv_snap) > max_len:
            csv_text += '\n[TRUNCATED]'
        csv_message = textwrap.dedent(f"""
            Database snapshot (CSV) for department {department}.
            The CSV has a header row with column names. Use this data to answer the owner's question.

            {csv_text}
        """)
        messages.append({'role': 'system', 'content': csv_message})
    elif snapshot_lines:
        messages.append({'role': 'system', 'content': 'Database snapshot for department ' + department + ':\n' + '\n'.join(snapshot_lines)})

    # If a language was detected from audio, instruct model to reply in that language
    if 'detected_language' in locals() and detected_language:
        # Provide a short system hint to prefer the detected language
        if detected_language and detected_language != 'unknown':
            messages.append({'role': 'system', 'content': f'Prefer replying in language: {detected_language}.'})

    messages.append({'role': 'user', 'content': user_message})

    openai_key = current_app.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    model = current_app.config.get('OPENAI_MODEL') or os.getenv('OPENAI_MODEL') or 'gpt-4o-mini'
    if not openai_key:
        # mock behavior
        return jsonify({'reply': f'[Mock AI reply for {department}] {user_message}'}), 200

    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}

    # Sanity check: ensure headers are encodable to latin-1 (http.client requirement).
    # If a header contains non-Latin-1 characters (e.g. Cyrillic pasted into the API key),
    # http.client will raise a UnicodeEncodeError. Detect this early and return a clear message.
    try:
        for hn, hv in headers.items():
            if not isinstance(hv, str):
                hv = str(hv)
            hv.encode('latin-1')
    except UnicodeEncodeError:
        current_app.logger.error('OpenAI header contains non-Latin-1 characters', exc_info=True)
        return jsonify({
            'error': 'invalid_openai_header',
            'detail': 'One of the HTTP headers (likely Authorization) contains non-Latin-1 characters. Please check your OPENAI_API_KEY for accidental non-ASCII characters or quotes.'
        }), 500
    payload = {'model': model, 'messages': messages, 'temperature': 0.2, 'max_tokens': 800}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        reply = ''
        if 'choices' in j and len(j['choices']) > 0:
            reply = j['choices'][0].get('message', {}).get('content', '')
        else:
            reply = j.get('error', {}).get('message', 'No reply')
        return jsonify({'reply': reply})
    except requests.RequestException:
        current_app.logger.exception('OpenAI request failed')
        return jsonify({'error': 'OpenAI request failed'}), 500


@bp.route('/delivery')
def delivery():
    return render_template('pages/delivery.html')


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
    """Endpoint to simulate a successful payment webhook for testing.

    Marks the order as PAID, commits, then calls `prepare_shipment` so warehouse
    tasks and shipments are created during testing.
    """
    from ...services.prepare_shipment import prepare_shipment

    order = Order.query.get(order_id)
    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for('shop_public.profile'))

    # Mark order as paid for testing and commit so prepare_shipment proceeds
    order.status = OrderStatus.PAID
    db.session.commit()

    prepare_shipment(order_id)
    flash("Webhook simulated: order marked PAID and shipment prepared.", "info")
    return redirect(url_for('shop_public.profile'))
