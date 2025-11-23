# file: backend/services/b2b_checks/b2b_service.py

from typing import Optional
import json

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
        website=getattr(user, 'company_website', None),
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
        screenshot_path=osint_res.get('screenshot'),
        score=score,
    )
    db.session.add(result)
    db.session.commit()

    # If problems detected, create an admin alert for review (do not block flow)
    try:
        problems = []
        if is_sanctioned:
            problems.append('sanctioned')
        if not is_valid_vat:
            problems.append('invalid_vat')
        if not is_company_found:
            problems.append('not_in_registry')
        if score is not None and score < 50:
            problems.append('low_score')

        if problems:
            from datetime import datetime
            payload = {
                'user_id': user.id,
                'problems': problems,
                'score': score,
                'raw_vies': vies_res,
                'raw_registry': registry_res,
                'raw_osint': osint_res,
            }

            # Insert into existing alerts table. Use textual JSON if needed.
            try:
                db.session.execute(
                    """
                    INSERT INTO alerts (type, channel, target, payload, is_sent, created_at)
                    VALUES (:type, :channel, :target, :payload, :is_sent, :created_at)
                    """,
                    {
                        'type': 'b2b_check',
                        'channel': 'admin',
                        'target': None,
                        'payload': json.dumps(payload),
                        'is_sent': False,
                        'created_at': datetime.utcnow(),
                    },
                )
                db.session.commit()
            except Exception:
                # fallback: try inserting payload as string
                try:
                    db.session.rollback()
                    db.session.execute(
                        """
                        INSERT INTO alerts (type, channel, target, payload, is_sent, created_at)
                        VALUES (:type, :channel, :target, :payload, :is_sent, :created_at)
                        """,
                        {
                            'type': 'b2b_check',
                            'channel': 'admin',
                            'target': None,
                            'payload': str(payload),
                            'is_sent': False,
                            'created_at': datetime.utcnow(),
                        },
                    )
                    db.session.commit()
                except Exception:
                    db.session.rollback()
    except Exception:
        # Never raise to caller — B2B checks mustn't break registration
        try:
            db.session.rollback()
        except Exception:
            pass

    return result
