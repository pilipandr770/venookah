# file: backend/models/inventory.py

from datetime import datetime

from ..extensions import db


class StockItem(db.Model):
    """
    Lagerbestände für jedes Produkt.
    """

    __tablename__ = "stock_items"
    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("venookah2.products.id"), nullable=False)
    product = db.relationship("Product", backref="stock_items")

    # Gesamtbestand für dieses Lager
    quantity_total = db.Column(db.Integer, nullable=False, default=0)
    quantity_reserved = db.Column(db.Integer, nullable=False, default=0)

    location = db.Column(db.String(255), nullable=True)  # Lagername / Bereich

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def available(self) -> int:
        return max(0, self.quantity_total - self.quantity_reserved)
