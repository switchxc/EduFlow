#!/usr/bin/env python3
"""
Скрипт для тестирования платежной системы cysu

Использование:
    python scripts/test_payment.py

Тестирует:
- Создание платежей
- Проверку статуса платежей
- Работу с ЮKassa API
- Симуляцию платежей
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models import User, Payment
from app.utils.payment_service import YooKassaService
from datetime import datetime, timedelta
from scripts.test_utils import global_cleanup


def test_payment_service() -> None:
    """Тестирует основные функции платежного сервиса"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Тестирование платежной системы cysu")
        print("=" * 60)
        
        # Создаем тестового пользователя
        test_user = create_test_user()
        
        # Тестируем сервис
        payment_service = YooKassaService()
        
        print(f"\n📋 Конфигурация платежного сервиса:")
        print(f"   - Shop ID: {payment_service.shop_id}")
        print(f"   - Режим симуляции: {payment_service.simulation_mode}")
        print(f"   - Base URL: {payment_service.base_url}")
        
        # Тест 1: Создание платежа
        print(f"\n🔧 Тест 1: Создание платежа")
        test_create_payment(payment_service, test_user)
        
        # Тест 2: Проверка статуса платежа
        print(f"\n🔍 Тест 2: Проверка статуса платежа")
        test_payment_status(payment_service, test_user)
        
        # Тест 3: Обработка успешного платежа
        print(f"\n✅ Тест 3: Обработка успешного платежа")
        test_successful_payment(payment_service, test_user)
        
        # Тест 4: Проверка подписки пользователя
        print(f"\n👤 Тест 4: Проверка подписки пользователя")
        test_user_subscription(payment_service, test_user)
        
        # Очистка тестовых данных
        print(f"\n🧹 Очистка тестовых данных")
        cleanup_test_data(test_user)
        
        print(f"\n🎉 Тестирование завершено!")


def create_test_user() -> User:
    """Создает тестового пользователя"""
    username = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    email = f"{username}@test.com"
    
    # Проверяем, существует ли пользователь
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return existing_user
    
    user = User(
        username=username,
        email=email,
        password="test_password",
        is_verified=True,
        is_subscribed=False
    )
    
    db.session.add(user)
    db.session.commit()
    
    print(f"   ✅ Создан тестовый пользователь: {username}")
    return user


def test_create_payment(payment_service: YooKassaService, user: User) -> None:
    """Тестирует создание платежа"""
    try:
        return_url = "http://localhost:5000/payment/success"
        
        # Тестируем создание платежа с разными ценами
        prices = [99.0, 249.0, 449.0, 749.0]
        
        for price in prices:
            print(f"   💰 Создание платежа на {price}₽...")
            
            result = payment_service.create_smart_payment(
                user=user,
                return_url=return_url,
                price=price
            )
            
            if "error" in result:
                print(f"      ❌ Ошибка: {result['error']}")
            else:
                print(f"      ✅ Платеж создан: ID={result['payment_id']}")
                print(f"         URL: {result['payment_url']}")
                print(f"         Статус: {result['status']}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при создании платежа: {e}")


def test_payment_status(payment_service: YooKassaService, user: User) -> None:
    """Тестирует проверку статуса платежа"""
    try:
        # Находим последний платеж пользователя
        payment = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).first()
        
        if not payment:
            print("   ⚠️  Нет платежей для проверки статуса")
            return
        
        print(f"   🔍 Проверка статуса платежа: {payment.yookassa_payment_id}")
        
        status = payment_service.get_payment_status(payment.yookassa_payment_id)
        
        if "error" in status:
            print(f"      ❌ Ошибка: {status['error']}")
        else:
            print(f"      ✅ Статус: {status['status']}")
            print(f"         Сумма: {status['amount']} {status['currency']}")
            print(f"         Оплачен: {status['paid']}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке статуса: {e}")


def test_successful_payment(payment_service: YooKassaService, user: User) -> None:
    """Тестирует обработку успешного платежа"""
    try:
        # Находим последний платеж пользователя
        payment = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).first()
        
        if not payment:
            print("   ⚠️  Нет платежей для обработки")
            return
        
        print(f"   ✅ Обработка платежа: {payment.yookassa_payment_id}")
        
        # В симуляционном режиме помечаем платеж как успешный
        if payment_service.simulation_mode:
            payment.status = "succeeded"
            payment.updated_at = datetime.utcnow()
            db.session.commit()
            print("      📝 Платеж помечен как успешный (симуляция)")
        
        result = payment_service.process_successful_payment(payment.yookassa_payment_id)
        
        if result:
            print("      ✅ Платеж успешно обработан")
        else:
            print("      ❌ Ошибка при обработке платежа")
        
    except Exception as e:
        print(f"   ❌ Ошибка при обработке платежа: {e}")


def test_user_subscription(payment_service: YooKassaService, user: User) -> None:
    """Тестирует проверку подписки пользователя"""
    try:
        print(f"   👤 Проверка подписки пользователя: {user.username}")
        
        # Обновляем данные пользователя из БД
        db.session.refresh(user)
        
        print(f"      Подписка активна: {user.is_subscribed}")
        if user.subscription_expires:
            print(f"      Истекает: {user.subscription_expires}")
            print(f"      Осталось дней: {(user.subscription_expires - datetime.utcnow()).days}")
        
        # Тестируем функцию проверки подписки
        is_active = payment_service.check_user_subscription(user)
        print(f"      Проверка через сервис: {is_active}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке подписки: {e}")


def cleanup_test_data(user: User) -> None:
    """Очищает тестовые данные"""
    try:
        print("   🧹 Очистка тестовых данных...")
        
        # Удаляем все платежи пользователя
        payments = Payment.query.filter_by(user_id=user.id).all()
        payments_count = len(payments)
        
        for payment in payments:
            try:
                db.session.delete(payment)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении платежа {payment.id}: {e}")
        
        # Удаляем пользователя
        try:
            db.session.delete(user)
        except Exception as e:
                print(f"      ⚠️ Ошибка при удалении пользователя: {e}")
        
        # Фиксируем изменения
        db.session.commit()
        
        print(f"   ✅ Удалено {payments_count} платежей")
        print(f"   ✅ Удален тестовый пользователь: {user.username}")
        
        # Дополнительная проверка - удаляем по паттерну на случай, если что-то осталось
        cleanup_by_pattern()
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке: {e}")
        db.session.rollback()


def cleanup_by_pattern() -> None:
    """Дополнительная очистка по паттернам имен"""
    try:
        # Удаляем пользователей по паттерну
        test_users = User.query.filter(User.username.like('test_user_%')).all()
        for user in test_users:
            try:
                # Удаляем связанные платежи
                Payment.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении тестового пользователя {user.username}: {e}")
        
        # Удаляем платежи без пользователей (orphaned)
        orphaned_payments = Payment.query.filter(~Payment.user_id.in_([u.id for u in User.query.all()])).all()
        for payment in orphaned_payments:
            try:
                db.session.delete(payment)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении orphaned платежа {payment.id}: {e}")
        
        db.session.commit()
        
        if test_users or orphaned_payments:
            print(f"   🧹 Дополнительная очистка: удалено {len(test_users)} пользователей, {len(orphaned_payments)} платежей")
        
    except Exception as e:
        print(f"      ⚠️ Ошибка при дополнительной очистке: {e}")
        db.session.rollback()


def main() -> None:
    """Главная функция скрипта"""
    try:
        test_payment_service()
        
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


if __name__ == "__main__":
    main() 