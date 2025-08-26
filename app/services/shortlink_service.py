from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple
import re

from .. import db
from ..models import ShortLink, ShortLinkRule


def normalize_url(raw_url: str) -> str:
    """Возвращает URL с http-схемой, если схема отсутствует."""
    url = raw_url.strip()
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return f"http://{url}"
    return url


def parse_ttl(ttl_value: str) -> Optional[datetime]:
    """Парсит TTL ('3h'/'6h'/'') в абсолютное время истечения."""
    ttl_value = (ttl_value or "").strip().lower()
    if ttl_value == "3h":
        return datetime.utcnow() + timedelta(hours=3)
    if ttl_value == "6h":
        return datetime.utcnow() + timedelta(hours=6)
    return None


def parse_max_clicks(value: str) -> Optional[int]:
    """Парсит ограничение по кликам из строки в int или None."""
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def create_short_link(original_url: str, ttl: str = "", max_clicks: str = "") -> ShortLink:
    """Создает короткую ссылку и при необходимости правило ограничения."""
    normalized = normalize_url(original_url)
    link = ShortLink.create_unique(normalized)

    expires_at = parse_ttl(ttl)
    limit_clicks = parse_max_clicks(max_clicks)

    if expires_at or limit_clicks is not None:
        rule = ShortLinkRule(short_link_id=link.id, expires_at=expires_at, max_clicks=limit_clicks)
        db.session.add(rule)
        db.session.commit()

    return link


def update_rule(link: ShortLink, ttl: str = "", max_clicks: str = "") -> None:
    """Обновляет/создает правило ограничения для короткой ссылки."""
    expires_at = parse_ttl(ttl)
    limit_clicks = parse_max_clicks(max_clicks)

    if link.rule is None:
        if expires_at or limit_clicks is not None:
            db.session.add(ShortLinkRule(short_link_id=link.id, expires_at=expires_at, max_clicks=limit_clicks))
    else:
        link.rule.expires_at = expires_at
        link.rule.max_clicks = limit_clicks
    db.session.commit()


def check_access(link: ShortLink) -> Tuple[bool, Optional[str]]:
    """Проверяет, можно ли перейти по ссылке.

    Возвращает (allowed, reason), где reason: 'expired_time' | 'expired_clicks' | None
    """
    if link.rule:
        if link.rule.expires_at and datetime.utcnow() > link.rule.expires_at:
            return False, "expired_time"
        if link.rule.max_clicks is not None and link.clicks >= link.rule.max_clicks:
            return False, "expired_clicks"
    return True, None


def register_click(link: ShortLink) -> None:
    """Увеличивает счётчик кликов и сохраняет в БД."""
    link.clicks += 1
    db.session.commit()


def reset_clicks(link: ShortLink) -> None:
    """Сбрасывает счётчик кликов ссылки."""
    link.clicks = 0
    db.session.commit()


def delete_short_link(link: ShortLink) -> None:
    """Удаляет короткую ссылку и связанные объекты."""
    db.session.delete(link)
    db.session.commit()


