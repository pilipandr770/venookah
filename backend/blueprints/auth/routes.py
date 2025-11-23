# file: backend/blueprints/auth/routes.py

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_user, logout_user, current_user, login_required

from ...extensions import db
from ...models.user import User, UserRole
from ...services.b2b_checks.b2b_service import run_b2b_checks_for_user
from ...services.crm_service import (
    get_or_create_company_for_b2b_user,
    create_primary_contact_for_company,
)
from . import bp
from .forms import LoginForm, RegisterForm


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("Ви вже увійшли в систему.", "info")
        return redirect(url_for("shop_public.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email_lower = form.email.data.lower()
        user = User.query.filter_by(email=email_lower).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Акаунт деактивовано. Зверніться до адміністратора.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user, remember=form.remember_me.data)
            flash("Ви успішно увійшли.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("shop_public.index"))

        flash("Невірний email або пароль.", "danger")

    else:
        print(f"DEBUG: Form not valid. Errors: {form.errors}")

    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("shop_public.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("Користувач з таким email вже існує.", "warning")
            return redirect(url_for("auth.register"))

        account_type = form.account_type.data
        if account_type == "b2b":
            role = UserRole.B2B
            is_b2b = True
        else:
            role = UserRole.B2C
            is_b2b = False

        user = User(
            email=form.email.data.lower(),
            first_name=form.first_name.data or None,
            last_name=form.last_name.data or None,
            company_name=form.company_name.data or None,
            vat_number=form.vat_number.data or None,
            handelsregister=form.handelsregister.data or None,
            country=form.country.data or None,
            city=form.city.data or None,
            address=form.address.data or None,
            postal_code=form.postal_code.data or None,
            role=role,
            is_b2b=is_b2b,
            is_confirmed=True,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # ---- АВТО-ПЕРЕВІРКА B2B + ДОДАВАННЯ В CRM ----
        if is_b2b:
            # 1) B2B-перевірка (VIES + реєстри + OSINT)
            result = run_b2b_checks_for_user(user)

            # 2) Створення компанії + базового контакту в CRM
            company = get_or_create_company_for_b2b_user(user)
            create_primary_contact_for_company(user, company)

            # 3) Можемо показати коротке повідомлення
            score = result.score if result else "N/A"
            flash(
                f"Ваш акаунт B2B зареєстровано. Результат перевірки контрагента (score): {score}.",
                "info",
            )
        else:
            flash("Реєстрація успішна. Тепер увійдіть у систему.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з акаунта.", "info")
    return redirect(url_for("shop_public.index"))


@bp.route('/account/delete', methods=['GET'])
@login_required
def delete_account_confirm():
    """Show account deletion confirmation page."""
    return render_template('auth/delete_account.html')


@bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Perform a safe account deletion / anonymization and logout the user.

    For legal/data-retention reasons we anonymize personal fields and
    deactivate the account rather than dropping rows that may be required
    for order history and accounting.
    """
    user = User.query.get(current_user.id)
    if not user:
        flash('Пользователь не найден.', 'warning')
        return redirect(url_for('shop_public.index'))

    # Anonymize personal data
    safe_email = f'deleted+{user.id}@venookah.local'
    user.email = safe_email
    user.first_name = None
    user.last_name = None
    user.company_name = None
    user.vat_number = None
    user.handelsregister = None
    user.country = None
    user.city = None
    user.address = None
    user.postal_code = None
    user.is_active = False
    user.is_confirmed = False
    # Remove password and any tokens
    try:
        user.password_hash = None
    except Exception:
        pass

    # Optionally revoke sessions / tokens here (implementation-specific)

    db.session.add(user)
    db.session.commit()

    # Log the user out after deletion
    logout_user()
    flash('Ваш аккаунт был удалён (анонимизирован). Если вы хотите восстановить данные, свяжитесь с поддержкой.', 'info')
    return redirect(url_for('shop_public.index'))


@bp.route("/bootstrap-superadmin", methods=["GET"])
def bootstrap_superadmin():
    """
    Одноразовий маршрут для створення SUPERADMIN, якщо ще немає.
    Використовувати тільки в dev, потім закрити.
    """
    existing_superadmin = User.query.filter_by(role=UserRole.SUPERADMIN).first()
    if existing_superadmin:
        return "Суперадмін вже існує.", 200

    email = "owner@example.com"
    password = "ChangeMe123!"

    user = User(
        email=email.lower(),
        first_name="Owner",
        last_name="Venookah",
        role=UserRole.SUPERADMIN,
        is_b2b=True,
        is_confirmed=True,
        module_permissions=None,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return f"Суперадміна створено: {email} / {password}", 200
