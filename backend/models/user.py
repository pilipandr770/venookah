# file: backend/models/user.py

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class UserRole:
    """Ролі користувачів у системі."""

    SUPERADMIN = "superadmin"  # власник бізнесу, має всі права
    ADMIN = "admin"            # адмін з модульними правами
    WAREHOUSE_ADMIN = "warehouse_admin"  # адмін складу
    B2B = "b2b"                # бізнес-клієнт (оптовий)
    B2C = "b2c"                # приватний клієнт (роздріб)


class User(db.Model, UserMixin):
    """
    Базова модель користувача.

    Права доступу до модулів (наприклад: "inventory", "orders", "crm")
    зберігаємо в JSON-полі module_permissions, щоб власник міг гнучко
    видавати доступи іншим адміністраторам.
    """

    __tablename__ = "users"
    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # main profile
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    company_name = db.Column(db.String(255))
    phone = db.Column(db.String(64))

    # тип користувача (див. UserRole)
    role = db.Column(db.String(32), nullable=False, default=UserRole.B2C)

    # B2B / B2C подальші налаштування
    is_b2b = db.Column(db.Boolean, nullable=False, default=False)
    vat_number = db.Column(db.String(64))      # VAT / USt-IdNr
    handelsregister = db.Column(db.String(64)) # Handelsregister
    country = db.Column(db.String(64))
    city = db.Column(db.String(128))
    address = db.Column(db.String(255))
    postal_code = db.Column(db.String(32))

    # модульні права у вигляді JSON:
    # {"inventory": true, "orders": true, "crm": false, "shipping": true}
    module_permissions = db.Column(db.JSON, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"

    # ---- Flask-Login ----

    @property
    def is_authenticated(self):
        return True

    # is_active вже є полем, Flask-Login його використовує

    # ---- Password helpers ----

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # ---- Roles & Permissions ----

    def has_role(self, role: str) -> bool:
        return self.role == role

    def is_superadmin(self) -> bool:
        return self.role == UserRole.SUPERADMIN

    def has_module_permission(self, module_name: str) -> bool:
        """
        Перевірка доступу до модуля.

        SUPERADMIN завжди має всі права.
        Для ADMIN дивимось module_permissions.
        Для B2B/B2C за замовчуванням False (крім того, що явно дозволимо).
        """
        if self.is_superadmin():
            return True

        if not self.module_permissions:
            return False

        return bool(self.module_permissions.get(module_name, False))
