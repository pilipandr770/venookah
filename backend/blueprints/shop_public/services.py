# file: backend/blueprints/shop_public/services.py

from ...models.product import Product


def get_active_products(limit: int | None = None):
    """
    Повертає активні товари для публічного магазину.
    """
    q = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc())
    if limit:
        q = q.limit(limit)
    return q.all()


def get_product_by_slug(slug: str) -> Product | None:
    """
    Повертає товар по slug або None.
    """
    return Product.query.filter_by(slug=slug, is_active=True).first()
