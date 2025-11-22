# file: backend/services/crm_service.py

from typing import Optional

from ..extensions import db
from ..models.crm import Company, Contact
from ..models.user import User


def get_or_create_company_for_b2b_user(user: User) -> Company:
    """
    Створює або повертає компанію, прив’язану до B2B-користувача.
    """
    if not user.is_b2b:
        raise ValueError("Користувач не є B2B, CRM-компанія не потрібна")

    company = Company.query.filter_by(user_id=user.id).first()
    if company:
        return company

    company = Company(
        name=user.company_name or user.email,
        vat_number=user.vat_number,
        country=user.country,
        city=user.city,
        address=user.address,
        postal_code=user.postal_code,
        user_id=user.id,
    )
    db.session.add(company)
    db.session.commit()
    return company


def create_primary_contact_for_company(user: User, company: Company) -> Optional[Contact]:
    """
    Створює базовий контакт під B2B-користувача (якщо ще немає).
    """
    if not user.email:
        return None

    existing = Contact.query.filter_by(company_id=company.id, email=user.email).first()
    if existing:
        return existing

    contact = Contact(
        company_id=company.id,
        name=f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
        email=user.email,
        phone=user.phone,
        role="owner",
    )
    db.session.add(contact)
    db.session.commit()
    return contact
