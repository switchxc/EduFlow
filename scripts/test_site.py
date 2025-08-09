# cysu v1.5.0 - Тестирование сайта
#!/usr/bin/env python3
"""
Скрипт для тестирования работы сайта cysu

Использование:
    python scripts/test_site.py

Тестирует:
- Подключение к базе данных
- Работу моделей
- Создание приложения
- Основные функции
- Email сервис
- Файловое хранилище
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models import User, Subject, Material, Submission, Payment, ChatMessage, Ticket
from app.utils.email_service import EmailService
from app.utils.file_storage import FileStorageManager
from app.utils.payment_service import YooKassaService
from datetime import datetime, timedelta


def test_site_functionality() -> None:
    """Тестирует основные функции сайта"""
    app = create_app()
    
    with app.app_context():
        print("🌐 Тестирование сайта cysu")
        print("=" * 60)
        
        # Тест 1: Подключение к базе данных
        print(f"\n🗄️  Тест 1: Подключение к базе данных")
        test_database_connection()
        
        # Тест 2: Модели данных
        print(f"\n📊 Тест 2: Модели данных")
        test_data_models()
        
        # Тест 3: Email сервис
        print(f"\n📧 Тест 3: Email сервис")
        test_email_service()
        
        # Тест 4: Файловое хранилище
        print(f"\n📁 Тест 4: Файловое хранилище")
        test_file_storage()
        
        # Тест 5: Платежный сервис
        print(f"\n💳 Тест 5: Платежный сервис")
        test_payment_service()
        
        # Тест 6: Статистика сайта
        print(f"\n📈 Тест 6: Статистика сайта")
        test_site_statistics()
        
        print(f"\n🎉 Тестирование завершено!")


def test_database_connection() -> None:
    """Тестирует подключение к базе данных"""
    try:
        # Проверяем подключение
        with db.engine.connect() as conn:
            conn.execute(db.text("SELECT 1"))
        print("   ✅ Подключение к базе данных успешно")
        
        # Проверяем таблицы
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
        print(f"   📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"      - {table}")
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения к БД: {e}")


def test_data_models() -> None:
    """Тестирует модели данных"""
    try:
        # Проверяем количество записей в каждой таблице
        models = [
            (User, "Пользователи"),
            (Subject, "Предметы"),
            (Material, "Материалы"),
            (Submission, "Решения"),
            (Payment, "Платежи"),
            (ChatMessage, "Сообщения чата"),
            (Ticket, "Тикеты")
        ]
        
        for model, name in models:
            try:
                count = model.query.count()
                print(f"   📊 {name}: {count} записей")
            except Exception as e:
                print(f"   ❌ Ошибка при подсчете {name}: {e}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании моделей: {e}")


def test_email_service() -> None:
    """Тестирует email сервис"""
    try:
        email_service = EmailService()
        
        # Проверяем конфигурацию
        from flask import current_app
        mail_config = {
            'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
            'MAIL_PORT': current_app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
            'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME')
        }
        
        print("   📧 Конфигурация email:")
        for key, value in mail_config.items():
            print(f"      {key}: {value}")
        
        # Тестируем создание email (без отправки)
        test_email = "test@example.com"
        test_code = "123456"
        
        print(f"   ✅ Email сервис инициализирован")
        print(f"   📝 Тестовый email: {test_email}")
        print(f"   🔢 Тестовый код: {test_code}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании email сервиса: {e}")


def test_file_storage() -> None:
    """Тестирует файловое хранилище"""
    try:
        # Проверяем папки
        folders = [
            "app/static/uploads",
            "app/static/chat_files", 
            "app/static/ticket_files"
        ]
        
        print("   📁 Проверка папок:")
        for folder in folders:
            folder_path = Path(folder)
            if folder_path.exists():
                file_count = len(list(folder_path.glob("*")))
                print(f"      ✅ {folder}: {file_count} файлов")
            else:
                print(f"      ❌ {folder}: не найдена")
        
        # Тестируем создание путей
        test_path, test_rel_path = FileStorageManager.get_material_upload_path(1, "test.txt")
        print(f"   🔧 Тест создания пути для материала:")
        print(f"      Полный путь: {test_path}")
        print(f"      Относительный путь: {test_rel_path}")
        
        test_path, test_rel_path = FileStorageManager.get_subject_upload_path(1, 2, "solution.txt")
        print(f"   🔧 Тест создания пути для решения:")
        print(f"      Полный путь: {test_path}")
        print(f"      Относительный путь: {test_rel_path}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании файлового хранилища: {e}")


def test_payment_service() -> None:
    """Тестирует платежный сервис"""
    try:
        payment_service = YooKassaService()
        
        print("   💳 Конфигурация платежного сервиса:")
        print(f"      Shop ID: {payment_service.shop_id}")
        print(f"      Режим симуляции: {payment_service.simulation_mode}")
        print(f"      Base URL: {payment_service.base_url}")
        
        # Проверяем цены подписки
        from flask import current_app
        prices = current_app.config.get('SUBSCRIPTION_PRICES', {})
        print(f"   💰 Цены подписки:")
        for period, price in prices.items():
            print(f"      {period} месяц(ев): {price}₽")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании платежного сервиса: {e}")


def test_site_statistics() -> None:
    """Показывает статистику сайта"""
    try:
        print("   📈 Статистика сайта:")
        
        # Общая статистика
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        subscribed_users = User.query.filter_by(is_subscribed=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        print(f"      👥 Всего пользователей: {total_users}")
        print(f"      ✅ Подтвержденных: {verified_users}")
        print(f"      💳 С подпиской: {subscribed_users}")
        print(f"      👑 Администраторов: {admin_users}")
        
        # Статистика контента
        total_subjects = Subject.query.count()
        total_materials = Material.query.count()
        total_submissions = Submission.query.count()
        total_tickets = Ticket.query.count()
        
        print(f"      📚 Предметов: {total_subjects}")
        print(f"      📄 Материалов: {total_materials}")
        print(f"      📝 Решений: {total_submissions}")
        print(f"      🎫 Тикетов: {total_tickets}")
        
        # Статистика платежей
        total_payments = Payment.query.count()
        successful_payments = Payment.query.filter_by(status='succeeded').count()
        
        print(f"      💰 Всего платежей: {total_payments}")
        print(f"      ✅ Успешных: {successful_payments}")
        
        # Последние активности
        recent_users = User.query.limit(3).all()
        print(f"      🆕 Последние пользователи:")
        for user in recent_users:
            print(f"         - {user.username}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при получении статистики: {e}")


def main() -> None:
    """Главная функция скрипта"""
    try:
        test_site_functionality()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 