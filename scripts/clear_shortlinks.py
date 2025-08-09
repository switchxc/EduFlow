# cysu v1.5.0 - Тестирование сайта
#!/usr/bin/env python3
"""
Скрипт для быстрой очистки всех коротких ссылок (ShortLink) в базе данных cysu.

Использование:
    python3 scripts/clear_shortlinks.py --yes         # удалить без подтверждения
    python3 scripts/clear_shortlinks.py --dry-run     # показать, что будет удалено
    python3 scripts/clear_shortlinks.py --stats       # показать статистику и выйти

По умолчанию запросит подтверждение (введите YES), если флаг --yes не указан.
"""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ShortLink, ShortLinkRule


def print_stats() -> None:
    """Печатает текущую статистику по коротким ссылкам."""
    total_links = ShortLink.query.count()
    total_rules = ShortLinkRule.query.count()
    print("📊 Текущая статистика коротких ссылок:")
    print(f"   - Ссылок: {total_links}")
    print(f"   - Правил: {total_rules}")
    if total_links:
        print("   - Примеры (первые 5):")
        for sl in ShortLink.query.order_by(ShortLink.created_at.desc()).limit(5).all():
            print(f"     • {sl.id}: code={sl.code} clicks={sl.clicks} url={sl.original_url}")


def clear_all(confirm: bool, dry_run: bool) -> None:
    """Очищает все короткие ссылки и связанные правила.

    - confirm: если False и не указан --yes, попросит подтверждение.
    - dry_run: если True, только покажет что будет удалено.
    """
    total_links = ShortLink.query.count()
    total_rules = ShortLinkRule.query.count()

    if total_links == 0 and total_rules == 0:
        print("✅ База уже пуста: коротких ссылок нет")
        return

    print_stats()

    if dry_run:
        print("\n🧪 Режим dry-run: удаление НЕ выполнялось")
        return

    if not confirm:
        try:
            answer = input("\n⚠️  Введите 'YES' для подтверждения удаления всех коротких ссылок: ")
        except KeyboardInterrupt:
            print("\n❌ Операция отменена пользователем")
            sys.exit(1)
        if answer.strip() != "YES":
            print("❌ Операция отменена")
            sys.exit(1)

    # Удаляем сначала правила, затем ссылки (bulk delete, чтобы не зависеть от каскада)
    from sqlalchemy import delete

    db.session.execute(delete(ShortLinkRule))
    db.session.execute(delete(ShortLink))
    db.session.commit()

    print("\n✅ Все короткие ссылки и правила удалены")
    print_stats()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Очистка коротких ссылок cysu")
    parser.add_argument("--yes", action="store_true", help="Удалить без подтверждения")
    parser.add_argument("--dry-run", action="store_true", help="Показать, что будет удалено, без выполнения")
    parser.add_argument("--stats", action="store_true", help="Показать статистику и выйти")
    return parser.parse_args(argv)


def main(argv: list[str]) -> NoReturn:
    args = parse_args(argv)
    app = create_app()
    with app.app_context():
        if args.stats:
            print_stats()
            sys.exit(0)
        clear_all(confirm=args.yes, dry_run=args["dry_run"])  # type: ignore[index]
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])


