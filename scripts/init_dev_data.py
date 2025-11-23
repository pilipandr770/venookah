# file: scripts/init_dev_data.py

"""
Initialisierung von Testdaten: Grundkategorien + Produkte (Kohle, Tabak).
"""

from decimal import Decimal

from backend.app import create_app
from backend.extensions import db
from backend.models.product import Category, Product
from backend.models.inventory import StockItem
from backend.models.user import User, UserRole
from backend.models.warehouse import WarehouseCategory, WarehouseProduct, WarehouseTask, WarehouseTaskStatus
from backend.models.order import Order, OrderStatus


def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Benutzer
        users_data = [
            {"email": "superadmin@example.com", "first_name": "Super", "last_name": "Admin", "role": UserRole.SUPERADMIN, "password": "password"},
            {"email": "admin@example.com", "first_name": "Shop", "last_name": "Admin", "role": UserRole.ADMIN, "password": "password"},
            {"email": "warehouse@example.com", "first_name": "Warehouse", "last_name": "Admin", "role": UserRole.WAREHOUSE_ADMIN, "password": "password"},
            {"email": "customer@example.com", "first_name": "John", "last_name": "Doe", "role": UserRole.B2C, "password": "password"},
        ]

        for udata in users_data:
            u = User.query.filter_by(email=udata["email"]).first()
            if not u:
                u = User(
                    email=udata["email"],
                    first_name=udata["first_name"],
                    last_name=udata["last_name"],
                    role=udata["role"],
                    is_active=True,
                )
                u.set_password(udata["password"])
                db.session.add(u)

        db.session.commit()

        # Warehouse Categories
        w_coal_cat = WarehouseCategory.query.filter_by(name="Kohle").first()
        if not w_coal_cat:
            w_coal_cat = WarehouseCategory(name="Kohle", description="Kategorie für Kohle")
            db.session.add(w_coal_cat)

        w_tobacco_cat = WarehouseCategory.query.filter_by(name="Tabak").first()
        if not w_tobacco_cat:
            w_tobacco_cat = WarehouseCategory(name="Tabak", description="Kategorie für Tabak")
            db.session.add(w_tobacco_cat)

        db.session.commit()

        # Warehouse Products
        w_products_data = [
            {"sku": "VEN-COAL-10KG", "name": "Venookah Coal 10kg", "category": w_coal_cat, "quantity": 100, "location": "Shelf A1"},
            {"sku": "VEN-TOB-1KG", "name": "Venookah Tobacco 1kg", "category": w_tobacco_cat, "quantity": 50, "location": "Shelf B2"},
        ]

        for wpdata in w_products_data:
            wp = WarehouseProduct.query.filter_by(sku=wpdata["sku"]).first()
            if not wp:
                wp = WarehouseProduct(
                    sku=wpdata["sku"],
                    name=wpdata["name"],
                    description="Warehouse product for testing.",
                    category=wpdata["category"],
                    quantity=wpdata["quantity"],
                    location=wpdata["location"],
                )
                db.session.add(wp)

        db.session.commit()

        # Kategorien
        coal_cat = Category.query.filter_by(slug="coal").first()
        if not coal_cat:
            coal_cat = Category(name="Kohle", slug="coal")
            db.session.add(coal_cat)

        tobacco_cat = Category.query.filter_by(slug="tobacco").first()
        if not tobacco_cat:
            tobacco_cat = Category(name="Tabak (Shisha)", slug="tobacco")
            db.session.add(tobacco_cat)

        db.session.commit()

        # Produkte
        products_data = [
            {
                "name": "Venookah Premium Coal 10kg",
                "slug": "venookah-premium-coal-10kg",
                "category": coal_cat,
                "price_b2c": Decimal("29.90"),
                "price_b2b": Decimal("19.90"),
            },
            {
                "name": "Venookah Coco Coal 20kg",
                "slug": "venookah-coco-coal-20kg",
                "category": coal_cat,
                "price_b2c": Decimal("49.90"),
                "price_b2b": Decimal("34.90"),
            },
            {
                "name": "Venookah Hookah Tobacco 1kg",
                "slug": "venookah-hookah-tobacco-1kg",
                "category": tobacco_cat,
                "price_b2c": Decimal("39.90"),
                "price_b2b": Decimal("27.90"),
            },
        ]

        for pdata in products_data:
            p = Product.query.filter_by(slug=pdata["slug"]).first()
            if not p:
                p = Product(
                    name=pdata["name"],
                    slug=pdata["slug"],
                    description="Demo-Produkt zum Testen des Shops.",
                    category=pdata["category"],
                    price_b2c=pdata["price_b2c"],
                    price_b2b=pdata["price_b2b"],
                    currency="EUR",
                    is_active=True,
                )
                db.session.add(p)
                db.session.flush()

                stock = StockItem(
                    product_id=p.id,
                    quantity_total=500,
                    quantity_reserved=0,
                    location="main",
                )
                db.session.add(stock)

        db.session.commit()

        # Test Warehouse Task
        if not WarehouseTask.query.first():
            # Create a dummy task
            task = WarehouseTask(
                order_id=1,  # Assuming order id 1 exists, or adjust
                status=WarehouseTaskStatus.PENDING,
            )
            db.session.add(task)
            db.session.commit()

        print("Testdaten initialisiert.")


if __name__ == "__main__":
    main()
