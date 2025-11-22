# file: scripts/import_products_from_csv.py

"""
Імпорт товарів з CSV (MVP-заглушка).
"""

import csv
from decimal import Decimal
from pathlib import Path

from backend.app import create_app
from backend.extensions import db
from backend.models.product import Product, Category


def import_from_csv(csv_path: str):
    app = create_app()
    with app.app_context():
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                slug = row["slug"]
                name = row["name"]
                category_slug = row.get("category_slug", "other")

                category = Category.query.filter_by(slug=category_slug).first()
                if not category:
                    category = Category(name=category_slug, slug=category_slug)
                    db.session.add(category)
                    db.session.flush()

                product = Product.query.filter_by(slug=slug).first()
                if not product:
                    product = Product(
                        name=name,
                        slug=slug,
                        category=category,
                        price_b2c=Decimal(row.get("price_b2c", "0") or "0"),
                        price_b2b=Decimal(row.get("price_b2b", "0") or "0"),
                        currency=row.get("currency", "EUR"),
                        description=row.get("description", ""),
                        is_active=True,
                    )
                    db.session.add(product)

        db.session.commit()
        print("Імпорт товарів завершено.")


if __name__ == "__main__":
    import_from_csv("products.csv")
