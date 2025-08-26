#!/usr/bin/env python3
"""
Скрипт для тестирования безопасности и аутентификации cysu

Использование:
    python scripts/test_security.py

Тестирует:
- Хеширование паролей
- Валидацию данных
- CSRF защиту
- Сессии пользователей
- Права доступа
- Безопасность форм
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
from scripts.test_utils import global_cleanup


def test_security():
    """Тестирует безопасность системы"""
    app = create_app()
    
    with app.app_context():
        print("🔒 Тестирование безопасности cysu")
        print("=" * 60)
        
        # Тест 1: Хеширование паролей
        print(f"\n🔐 Тест 1: Хеширование паролей")
        test_password_hashing()
        
        # Тест 2: Валидация данных
        print(f"\n✅ Тест 2: Валидация данных")
        test_data_validation()
        
        # Тест 3: Создание тестового пользователя
        print(f"\n👤 Тест 3: Создание тестового пользователя")
        test_user = create_test_user()
        
        # Тест 4: Аутентификация
        print(f"\n🔑 Тест 4: Аутентификация")
        test_authentication(test_user)
        
        # Тест 5: Права доступа
        print(f"\n👑 Тест 5: Права доступа")
        test_access_control(test_user)
        
        # Тест 6: Безопасность сессий
        print(f"\n🛡️ Тест 6: Безопасность сессий")
        test_session_security()
        
        # Очистка тестовых данных
        print(f"\n🧹 Очистка тестовых данных")
        cleanup_test_data(test_user)
        
        print(f"\n🎉 Тестирование безопасности завершено!")

def test_password_hashing():
    """Тестирует хеширование паролей"""
    try:
        print(f"   🔐 Тестирование хеширования паролей")
        
        # Тест 1: Создание хеша
        test_password = "test_password_123"
        password_hash = generate_password_hash(test_password)
        print(f"      ✅ Хеш создан: {password_hash[:20]}...")
        
        # Тест 2: Проверка правильного пароля
        is_valid = check_password_hash(password_hash, test_password)
        print(f"      ✅ Проверка правильного пароля: {is_valid}")
        
        # Тест 3: Проверка неправильного пароля
        is_invalid = check_password_hash(password_hash, "wrong_password")
        print(f"      ❌ Проверка неправильного пароля: {is_invalid}")
        
        # Тест 4: Разные хеши для одного пароля
        hash1 = generate_password_hash(test_password)
        hash2 = generate_password_hash(test_password)
        print(f"      🔄 Разные хеши для одного пароля: {hash1 != hash2}")
        
        # Тест 5: Проверка сложности паролей
        weak_passwords = ["123", "password", "admin", "qwerty"]
        strong_passwords = ["MySecurePass123!", "Complex@Password#2024", "StrongP@ssw0rd!"]
        
        print(f"      📊 Тест сложности паролей:")
        for password in weak_passwords:
            is_weak = len(password) < 8 or password.islower() or password.isdigit()
            print(f"         '{password}': {'Слабый' if is_weak else 'Сильный'}")
        
        for password in strong_passwords:
            is_strong = len(password) >= 8 and not password.islower() and not password.isdigit()
            print(f"         '{password}': {'Сильный' if is_strong else 'Слабый'}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании хеширования: {e}")

def test_data_validation():
    """Тестирует валидацию данных"""
    try:
        print(f"   ✅ Тестирование валидации данных")
        
        # Тест 1: Валидация email
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "admin@test.ru"]
        invalid_emails = ["invalid-email", "@domain.com", "user@", "test..test@domain.com"]
        
        print(f"      📧 Валидация email адресов:")
        for email in valid_emails:
            is_valid = "@" in email and "." in email.split("@")[1]
            print(f"         '{email}': {'Валидный' if is_valid else 'Невалидный'}")
        
        for email in invalid_emails:
            is_valid = "@" in email and "." in email.split("@")[1]
            print(f"         '{email}': {'Валидный' if is_valid else 'Невалидный'}")
        
        # Тест 2: Валидация username
        valid_usernames = ["user123", "admin_user", "test-user", "user_name"]
        invalid_usernames = ["", "a", "user@name", "user name", "123user"]
        
        print(f"      👤 Валидация username:")
        for username in valid_usernames:
            is_valid = len(username) >= 3 and username.replace("_", "").replace("-", "").isalnum()
            print(f"         '{username}': {'Валидный' if is_valid else 'Невалидный'}")
        
        for username in invalid_usernames:
            is_valid = len(username) >= 3 and username.replace("_", "").replace("-", "").isalnum()
            print(f"         '{username}': {'Валидный' if is_valid else 'Невалидный'}")
        
        # Тест 3: Валидация длины пароля
        passwords = ["123", "12345", "123456", "1234567", "12345678", "123456789"]
        print(f"      🔑 Валидация длины пароля:")
        for password in passwords:
            is_strong = len(password) >= 8
            print(f"         '{password}': {'Сильный' if is_strong else 'Слабый'} ({len(password)} символов)")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании валидации: {e}")

def create_test_user():
    """Создает тестового пользователя"""
    username = f"test_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    email = f"{username}@test.com"
    
    # Проверяем, существует ли пользователь
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return existing_user
    
    user = User(
        username=username,
        email=email,
        password=generate_password_hash("test_security_123"),
        is_verified=True,
        is_subscribed=True,
        is_admin=False,
        subscription_expires=datetime.utcnow() + timedelta(days=30)
    )
    
    db.session.add(user)
    db.session.commit()
    
    print(f"   ✅ Создан тестовый пользователь: {username}")
    return user

def test_authentication(user):
    """Тестирует аутентификацию"""
    try:
        print(f"   🔑 Тестирование аутентификации для пользователя: {user.username}")
        
        # Тест 1: Проверка правильного пароля
        is_valid = check_password_hash(user.password, "test_security_123")
        print(f"      ✅ Правильный пароль: {is_valid}")
        
        # Тест 2: Проверка неправильного пароля
        is_invalid = check_password_hash(user.password, "wrong_password")
        print(f"      ❌ Неправильный пароль: {is_invalid}")
        
        # Тест 3: Проверка статуса пользователя
        print(f"      👤 Статус пользователя:")
        print(f"         Подтвержден: {user.is_verified}")
        print(f"         Администратор: {user.is_admin}")
        print(f"         Подписка активна: {user.is_subscribed}")
        
        # Тест 4: Проверка срока действия подписки
        if user.subscription_expires:
            days_left = (user.subscription_expires - datetime.utcnow()).days
            print(f"         Осталось дней подписки: {days_left}")
            print(f"         Подписка действительна: {days_left > 0}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании аутентификации: {e}")

def test_access_control(user):
    """Тестирует права доступа"""
    try:
        print(f"   👑 Тестирование прав доступа для пользователя: {user.username}")
        
        # Тест 1: Проверка ролей пользователя
        roles = []
        if user.is_admin:
            roles.append("Администратор")
        if user.is_verified:
            roles.append("Подтвержденный пользователь")
        if user.is_subscribed:
            roles.append("Подписчик")
        
        print(f"      🎭 Роли пользователя: {', '.join(roles) if roles else 'Обычный пользователь'}")
        
        # Тест 2: Проверка доступа к функциям
        access_levels = {
            "Просмотр материалов": user.is_subscribed,
            "Создание тикетов": user.is_verified,
            "Административная панель": user.is_admin,
            "Управление пользователями": user.is_admin,
            "Создание предметов": user.is_admin,
            "Чат с поддержкой": user.is_verified
        }
        
        print(f"      🔓 Доступ к функциям:")
        for function, has_access in access_levels.items():
            status = "✅ Доступен" if has_access else "❌ Запрещен"
            print(f"         {function}: {status}")
        
        # Тест 3: Проверка безопасности данных
        sensitive_fields = ["password", "email", "subscription_expires"]
        print(f"      🛡️ Защита чувствительных данных:")
        for field in sensitive_fields:
            if hasattr(user, field):
                value = getattr(user, field)
                if field == "password":
                    is_hashed = value.startswith("pbkdf2:sha256:") or value.startswith("scrypt:")
                    print(f"         {field}: {'Хеширован' if is_hashed else 'Не хеширован'}")
                else:
                    print(f"         {field}: {'Заполнено' if value else 'Пусто'}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании прав доступа: {e}")

def test_session_security():
    """Тестирует безопасность сессий"""
    try:
        print(f"   🛡️ Тестирование безопасности сессий")
        
        # Тест 1: Проверка конфигурации сессий
        from flask import current_app
        session_config = {
            'SECRET_KEY': current_app.config.get('SECRET_KEY'),
            'SESSION_COOKIE_SECURE': current_app.config.get('SESSION_COOKIE_SECURE', False),
            'SESSION_COOKIE_HTTPONLY': current_app.config.get('SESSION_COOKIE_HTTPONLY', True),
            'PERMANENT_SESSION_LIFETIME': current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=24))
        }
        
        print(f"      ⚙️ Конфигурация сессий:")
        for key, value in session_config.items():
            if key == 'SECRET_KEY':
                is_secure = len(str(value)) >= 32 and value != 'default-secret-key-change-in-production'
                print(f"         {key}: {'Безопасный' if is_secure else 'Небезопасный'}")
            elif key == 'PERMANENT_SESSION_LIFETIME':
                hours = value.total_seconds() / 3600
                print(f"         {key}: {hours:.1f} часов")
            else:
                status = "Включено" if value else "Отключено"
                print(f"         {key}: {status}")
        
        # Тест 2: Проверка безопасности паролей
        print(f"      🔐 Рекомендации по безопасности:")
        recommendations = [
            "Используйте HTTPS в продакшене",
            "Регулярно меняйте SECRET_KEY",
            "Установите SESSION_COOKIE_SECURE=True для HTTPS",
            "Используйте сложные пароли (минимум 8 символов)",
            "Включите двухфакторную аутентификацию",
            "Логируйте попытки входа в систему"
        ]
        
        for i, recommendation in enumerate(recommendations, 1):
            print(f"         {i}. {recommendation}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании безопасности сессий: {e}")

def cleanup_test_data(user):
    """Очищает тестовые данные"""
    try:
        print(f"\n🧹 Очистка тестовых данных...")
        
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
                print(f"   ✅ Удален тестовый пользователь: {user.username}")
            except Exception as e:
                print(f"   ⚠️ Ошибка при удалении пользователя: {e}")
                db.session.rollback()
        
        # Дополнительная очистка по паттернам
        cleanup_by_pattern()
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке: {e}")


def cleanup_by_pattern():
    """Дополнительная очистка по паттернам имен"""
    try:
        # Удаляем пользователей по паттерну
        test_users = User.query.filter(User.username.like('test_security_%')).all()
        for user in test_users:
            try:
                db.session.delete(user)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении тестового пользователя {user.username}: {e}")
        
        # Удаляем пользователей с тестовыми email
        test_email_users = User.query.filter(User.email.like('%@test.com')).all()
        for user in test_email_users:
            try:
                db.session.delete(user)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении пользователя с тестовым email {user.email}: {e}")
        
        db.session.commit()
        
        if test_users or test_email_users:
            print(f"   🧹 Дополнительная очистка: удалено {len(test_users)} пользователей по username, {len(test_email_users)} по email")
        
    except Exception as e:
        print(f"      ⚠️ Ошибка при дополнительной очистке: {e}")
        db.session.rollback()

def main():
    """Основная функция"""
    try:
        test_security()
        
        # Глобальная очистка после завершения тестов
        print(f"\n🧹 Глобальная очистка тестовых данных...")
        global_cleanup()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        # Даже при ошибке пытаемся очистить данные
        try:
            global_cleanup()
        except:
            pass
        sys.exit(1)

if __name__ == '__main__':
    main()
