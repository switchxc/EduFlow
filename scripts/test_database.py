#!/usr/bin/env python3
"""
Скрипт для тестирования базы данных и моделей cysu

Использование:
    python scripts/test_database.py

Тестирует:
- Подключение к базе данных
- Создание и удаление записей
- Связи между моделями
- Валидацию данных
- Производительность запросов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Subject, Material, Submission, Payment, Ticket, TicketMessage, Notification, ChatMessage
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import string

def test_database():
    """Тестирует базу данных и модели"""
    app = create_app()
    
    with app.app_context():
        print("🗄️ Тестирование базы данных cysu")
        print("=" * 60)
        
        # Тест 1: Подключение к базе данных
        print(f"\n🔧 Тест 1: Подключение к базе данных")
        test_database_connection()
        
        # Тест 2: Создание тестовых данных
        print(f"\n📝 Тест 2: Создание тестовых данных")
        test_data = create_test_data()
        
        # Тест 3: Связи между моделями
        print(f"\n🔗 Тест 3: Связи между моделями")
        test_model_relationships(test_data)
        
        # Тест 4: Валидация данных
        print(f"\n✅ Тест 4: Валидация данных")
        test_data_validation()
        
        # Тест 5: Производительность запросов
        print(f"\n⚡ Тест 5: Производительность запросов")
        test_query_performance()
        
        # Тест 6: Статистика базы данных
        print(f"\n📊 Тест 6: Статистика базы данных")
        test_database_statistics()
        
        # Очистка тестовых данных
        cleanup_test_data(test_data)
        
        print(f"\n🎉 Тестирование базы данных завершено!")

def test_database_connection():
    """Тестирует подключение к базе данных"""
    try:
        # Проверяем подключение
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT 1"))
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

def create_test_data():
    """Создает тестовые данные"""
    test_data = {}
    
    try:
        # Создаем тестового пользователя
        username = f"test_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user = User(
            username=username,
            email=f"{username}@test.com",
            password=generate_password_hash("test123"),
            is_verified=True,
            is_subscribed=True,
            subscription_expires=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(user)
        db.session.commit()
        test_data['user'] = user
        print(f"   ✅ Создан тестовый пользователь: {username}")
        
        # Создаем тестовый предмет
        subject = Subject(
            title=f"Тестовый предмет {datetime.now().strftime('%H%M%S')}",
            description="Описание тестового предмета",
            created_by=user.id
        )
        db.session.add(subject)
        db.session.commit()
        test_data['subject'] = subject
        print(f"   ✅ Создан тестовый предмет: {subject.title}")
        
        # Создаем тестовые материалы
        materials = []
        for i in range(3):
            material = Material(
                title=f"Тестовый материал {i+1}",
                description=f"Содержание тестового материала {i+1}",
                type="lecture" if i % 2 == 0 else "assignment",
                subject_id=subject.id,
                created_by=user.id
            )
            db.session.add(material)
            materials.append(material)
        
        db.session.commit()
        test_data['materials'] = materials
        print(f"   ✅ Создано {len(materials)} тестовых материалов")
        
        # Создаем тестовый тикет
        ticket = Ticket(
            subject="Тестовый тикет",
            description="Описание тестового тикета",
            user_id=user.id,
            status="open"
        )
        db.session.add(ticket)
        db.session.commit()
        test_data['ticket'] = ticket
        print(f"   ✅ Создан тестовый тикет: {ticket.subject}")
        
        # Создаем тестовое сообщение тикета
        message = TicketMessage(
            content="Тестовое сообщение в тикете",
            ticket_id=ticket.id,
            user_id=user.id,
            is_admin=False
        )
        db.session.add(message)
        db.session.commit()
        test_data['message'] = message
        print(f"   ✅ Создано тестовое сообщение тикета")
        
        # Создаем тестовый платеж
        payment = Payment(
            user_id=user.id,
            amount=99.0,
            currency="RUB",
            status="succeeded",
            yookassa_payment_id=f"test_payment_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        db.session.add(payment)
        db.session.commit()
        test_data['payment'] = payment
        print(f"   ✅ Создан тестовый платеж: {payment.amount}₽")
        
        return test_data
        
    except Exception as e:
        print(f"   ❌ Ошибка при создании тестовых данных: {e}")
        return {}

def test_model_relationships(test_data):
    """Тестирует связи между моделями"""
    try:
        user = test_data.get('user')
        subject = test_data.get('subject')
        materials = test_data.get('materials', [])
        ticket = test_data.get('ticket')
        payment = test_data.get('payment')
        
        if not user:
            print("   ⚠️  Тестовые данные не найдены")
            return
        
        print(f"   🔗 Проверка связей для пользователя: {user.username}")
        
        # Проверяем связь пользователь -> предметы
        user_subjects = Subject.query.filter_by(created_by=user.id).all()
        print(f"      📚 Предметы пользователя: {len(user_subjects)}")
        
        # Проверяем связь предмет -> материалы
        if subject:
            subject_materials = Material.query.filter_by(subject_id=subject.id).all()
            print(f"      📄 Материалы предмета: {len(subject_materials)}")
        
        # Проверяем связь пользователь -> тикеты
        user_tickets = Ticket.query.filter_by(user_id=user.id).all()
        print(f"      🎫 Тикеты пользователя: {len(user_tickets)}")
        
        # Проверяем связь тикет -> сообщения
        if ticket:
            ticket_messages = TicketMessage.query.filter_by(ticket_id=ticket.id).all()
            print(f"      💬 Сообщения тикета: {len(ticket_messages)}")
        
        # Проверяем связь пользователь -> платежи
        user_payments = Payment.query.filter_by(user_id=user.id).all()
        print(f"      💰 Платежи пользователя: {len(user_payments)}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке связей: {e}")

def test_data_validation():
    """Тестирует валидацию данных"""
    try:
        print(f"   ✅ Тестирование валидации данных")
        
        # Тест уникальности username
        try:
            duplicate_user = User(
                username="admin",  # Уже существует
                email="duplicate@test.com",
                password="test123"
            )
            db.session.add(duplicate_user)
            db.session.commit()
            print("      ❌ Ошибка: Дубликат username не должен быть создан")
        except Exception as e:
            print("      ✅ Валидация username работает корректно")
            db.session.rollback()
        
        # Тест обязательных полей
        try:
            invalid_user = User(
                username="",  # Пустое поле
                email="test@test.com",
                password="test123"
            )
            db.session.add(invalid_user)
            db.session.commit()
            print("      ❌ Ошибка: Пустой username не должен быть создан")
        except Exception as e:
            print("      ✅ Валидация обязательных полей работает корректно")
            db.session.rollback()
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании валидации: {e}")

def test_query_performance():
    """Тестирует производительность запросов"""
    try:
        print(f"   ⚡ Тестирование производительности запросов")
        
        # Тест подсчета записей
        import time
        start_time = time.time()
        user_count = User.query.count()
        end_time = time.time()
        print(f"      📊 Подсчет пользователей: {user_count} ({(end_time - start_time)*1000:.2f}ms)")
        
        # Тест сложного запроса
        start_time = time.time()
        active_users = User.query.filter_by(is_verified=True, is_subscribed=True).all()
        end_time = time.time()
        print(f"      👥 Активные пользователи: {len(active_users)} ({(end_time - start_time)*1000:.2f}ms)")
        
        # Тест JOIN запроса
        start_time = time.time()
        materials_with_subjects = db.session.query(Material, Subject).join(Subject).limit(10).all()
        end_time = time.time()
        print(f"      🔗 JOIN запрос: {len(materials_with_subjects)} записей ({(end_time - start_time)*1000:.2f}ms)")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании производительности: {e}")

def test_database_statistics():
    """Показывает статистику базы данных"""
    try:
        print(f"   📊 Статистика базы данных:")
        
        # Статистика по таблицам
        models = [
            (User, "Пользователи"),
            (Subject, "Предметы"),
            (Material, "Материалы"),
            (Submission, "Решения"),
            (Payment, "Платежи"),
            (Ticket, "Тикеты"),
            (TicketMessage, "Сообщения тикетов"),
            (Notification, "Уведомления"),
            (ChatMessage, "Сообщения чата")
        ]
        
        for model, name in models:
            try:
                count = model.query.count()
                print(f"      {name}: {count} записей")
            except Exception as e:
                print(f"      ❌ Ошибка при подсчете {name}: {e}")
        
        # Дополнительная статистика
        verified_users = User.query.filter_by(is_verified=True).count()
        subscribed_users = User.query.filter_by(is_verified=True, is_subscribed=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        print(f"      ✅ Подтвержденных пользователей: {verified_users}")
        print(f"      💳 Пользователей с подпиской: {subscribed_users}")
        print(f"      👑 Администраторов: {admin_users}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при получении статистики: {e}")

def cleanup_test_data(test_data):
    """Очищает тестовые данные"""
    try:
        print(f"\n🧹 Очистка тестовых данных...")
        
        user = test_data.get('user')
        if user:
            # Удаляем связанные данные
            TicketMessage.query.filter_by(user_id=user.id).delete()
            Payment.query.filter_by(user_id=user.id).delete()
            Ticket.query.filter_by(user_id=user.id).delete()
            Material.query.filter_by(created_by=user.id).delete()
            Subject.query.filter_by(created_by=user.id).delete()
            
            # Удаляем пользователя
            db.session.delete(user)
            db.session.commit()
            
            print(f"   ✅ Удалены все тестовые данные для пользователя: {user.username}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке: {e}")

def main():
    """Основная функция"""
    try:
        test_database()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
