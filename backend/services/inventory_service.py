# file: backend/services/inventory_service.py

from typing import Optional

from ..extensions import db
from ..models.inventory import StockItem
from ..models.product import Product


def get_stock_for_product(product_id: int) -> Optional[StockItem]:
    """
    Gibt den Lagerdatensatz für ein Produkt zurück oder None.
    """
    return StockItem.query.filter_by(product_id=product_id).first()


def ensure_stock_item(product: Product, location: str | None = None) -> StockItem:
    """
    Stellt sicher, dass ein Lagerdatensatz für das Produkt existiert.
    Falls nicht vorhanden, wird ein Eintrag mit Nullbestand angelegt.
    """
    stock = StockItem.query.filter_by(product_id=product.id).first()
    if not stock:
        stock = StockItem(
            product_id=product.id,
            quantity_total=0,
            quantity_reserved=0,
            location=location or "main",
        )
        db.session.add(stock)
        db.session.commit()
    return stock


def adjust_stock(product: Product, delta_quantity: int) -> StockItem:
    """
    Passt die Menge des Produkts im Lager um `delta_quantity` an.
    Kann positiv oder negativ sein.
    """
    stock = ensure_stock_item(product)
    stock.quantity_total = (stock.quantity_total or 0) + delta_quantity
    if stock.quantity_total < 0:
        stock.quantity_total = 0
    db.session.commit()
    return stock
