# file: backend/services/inventory_service.py

from typing import Optional

from ..extensions import db
from ..models.inventory import StockItem
from ..models.product import Product


def get_stock_for_product(product_id: int) -> Optional[StockItem]:
    """
    Повертає запис складу для товару або None.
    """
    return StockItem.query.filter_by(product_id=product_id).first()


def ensure_stock_item(product: Product, location: str | None = None) -> StockItem:
    """
    Гарантує, що для товару існує запис у складі.
    Якщо немає — створює з нульовим залишком.
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
    Коригує кількість товару на складі на delta_quantity.
    Може бути як додатна, так і від’ємна.
    """
    stock = ensure_stock_item(product)
    stock.quantity_total = (stock.quantity_total or 0) + delta_quantity
    if stock.quantity_total < 0:
        stock.quantity_total = 0
    db.session.commit()
    return stock
