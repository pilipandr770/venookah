# file: backend/services/b2b_checks/b2b_service.py

from typing import Optional

from ...extensions import db
from ...models.b2b_check import B2BCheckResult
from ...models.user import User
from .vies_client import check_vat
from .registry_clients import check_company_in_registry
from .osint_client import check_sanctions


def run_b2b_checks_for_user(user: User) -> Optional[B2BCheckResult]:
    """
    Запускає повний цикл перевірки B2B-клієнта:
    - VIES
    - нац. реєстр
    - OSINT / санкції

    і зберігає результат у таблицю b2b_check_results.
    """
    if not user.is_b2b:
        return None

    vat_number = user.vat_number or ""
    country = user.country or ""
    handelsregister = user.handelsregister or ""

    vies_res = check_vat(vat_number=vat_number, country_code=country)
    registry_res = check_company_in_registry(
        company_name=user.company_name,
        handelsregister=user.handelsregister,
        country_code=country,
    )
    osint_res = check_sanctions(
        vat_number=vat_number,
        company_name=user.company_name,
    )

    is_valid_vat = bool(vies_res.get("is_valid"))
    is_company_found = bool(registry_res.get("is_found"))
    is_sanctioned = bool(osint_res.get("is_sanctioned"))

    # простий скоринг
    score = 0
    if is_valid_vat:
        score += 40
    if is_company_found:
        score += 40
    if not is_sanctioned:
        score += 20

    result = B2BCheckResult(
        user_id=user.id,
        vat_number=vat_number or None,
        handelsregister=handelsregister or None,
        country=country or None,
        is_valid_vat=is_valid_vat,
        is_company_found=is_company_found,
        is_sanctioned=is_sanctioned,
        raw_vies=vies_res,
        raw_registry=registry_res,
        raw_osint=osint_res,
        score=score,
    )
    db.session.add(result)
    db.session.commit()
    return result
