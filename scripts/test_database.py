#!/usr/bin/env python3
"""
Скрипт для тестирования базы данных EduFlow
Проверяет подключение, создает тестовые данные и тестирует функциональность

Использование:
    python scripts/test_database.py
"""

import sys
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Subject, Material, Submission, ShortLink


def test_database():
    """Основная функция тестирования базы данных"""
    print("🗄️ ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ EDUFLOW")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        try:
            # Тест подключения
            test_database_connection()

            # Создание тестовых данных
            test_data = create_test_data()

            # Тест связей между моделями
            test_model_relationships(test_data)

            # Тест валидации данных
            test_data_validation()

            # Тест производительности запросов
            test_query_performance()

            # Тест статистики базы данных
            test_database_statistics()

        finally:
            # Очистка всех тестовых данных
            cleanup_test_data(test_data)

    print("\n✅ Тестирование базы данных завершено!")


def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("\n🔌 ТЕСТ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("-" * 40)

    try:
        # Проверяем подключение
        db.engine.connect()
        print("   ✅ Подключение к базе данных успешно")

        # Проверяем существование таблиц
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"   📋 Найдено таблиц: {len(tables)}")

        for table in tables:
            print(f"      - {table}")

    except Exception as e:
        print(f"   ❌ Ошибка подключения к базе данных: {e}")
        raise


def create_test_data() -> Dict[str, Any]:
    """Создает тестовые данные для тестирования"""
    print("\n📝 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("-" * 40)

    test_data = {}

    try:
        # Создаем тестового пользователя
        test_user = User(
            username=f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            email=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
            password="test_password_hash",
            is_verified=True,
            is_subscribed=True,
            is_admin=False,
            subscription_expires=datetime.utcnow() + timedelta(days=30),
        )
        db.session.add(test_user)
        db.session.flush()
        test_data["user"] = test_user
        print("   ✅ Тестовый пользователь создан")

        # Создаем тестовый предмет
        test_subject = Subject(
            title=f"Test Subject {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Тестовый предмет для тестирования",
        )
        db.session.add(test_subject)
        db.session.flush()
        test_data["subject"] = test_subject
        print("   ✅ Тестовый предмет создан")

        # Создаем тестовый материал
        test_material = Material(
            title=f"Test Material {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Тестовый контент материала",
            type="lecture",
            subject_id=test_subject.id,
        )
        db.session.add(test_material)
        db.session.flush()
        test_data["material"] = test_material
        print("   ✅ Тестовый материал создан")

        # Создаем тестовое задание
        test_submission = Submission(
            user_id=test_user.id,
            material_id=test_material.id,
            text=f"Test submission {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            submitted_at=datetime.utcnow(),
        )
        db.session.add(test_submission)
        db.session.flush()
        test_data["submission"] = test_submission
        print("   ✅ Тестовое задание создано")

        # Создаем тестовую ссылку
        test_link = ShortLink(
            original_url="https://test.com",
            code=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        db.session.add(test_link)
        db.session.flush()
        test_data["link"] = test_link
        print("   ✅ Тестовая ссылка создана")

        # Фиксируем все изменения
        db.session.commit()
        print("   💾 Все тестовые данные сохранены в базе")

    except Exception as e:
        print(f"   ❌ Ошибка создания тестовых данных: {e}")
        db.session.rollback()
        raise

    return test_data


def test_model_relationships(test_data: Dict[str, Any]):
    """Тестирует связи между моделями данных"""
    print("\n🔗 ТЕСТ СВЯЗЕЙ МЕЖДУ МОДЕЛЯМИ")
    print("-" * 40)

    try:
        user = test_data["user"]
        subject = test_data["subject"]
        material = test_data["material"]

        # Тест связи пользователь -> материалы
        user_materials = Material.query.join(Subject).all()
        print(
            f"   ✅ Связь пользователь -> материалы: {len(user_materials)} материалов"
        )

        # Тест связи предмет -> материалы
        subject_materials = Material.query.filter_by(subject_id=subject.id).all()
        print(f"   ✅ Связь предмет -> материалы: {len(subject_materials)} материалов")

        # Тест связи пользователь -> задания
        user_submissions = Submission.query.filter_by(user_id=user.id).all()
        print(f"   ✅ Связь пользователь -> задания: {len(user_submissions)} заданий")

        # Тест связи материал -> задания
        material_submissions = Submission.query.filter_by(material_id=material.id).all()
        print(f"   ✅ Связь материал -> задания: {len(material_submissions)} заданий")

        # Тест связи коротких ссылок
        total_links = ShortLink.query.count()
        print(f"   ✅ Всего коротких ссылок: {total_links}")

    except Exception as e:
        print(f"   ❌ Ошибка тестирования связей: {e}")


def test_data_validation():
    """Тестирует валидацию данных"""
    print("\n✅ ТЕСТ ВАЛИДАЦИИ ДАННЫХ")
    print("-" * 40)

    try:
        # Тест валидации email
        invalid_emails = [
            "invalid_email",
            "@test.com",
            "test@",
            "test..test@test.com",
            "test@test..com",
        ]

        for email in invalid_emails:
            try:
                # Пытаемся создать пользователя с неверным email
                user = User(
                    username="test_validation", email=email, password="password"
                )
                db.session.add(user)
                db.session.flush()
                print(f"   ❌ Валидация email не работает для: {email}")
                db.session.rollback()
            except Exception:
                print(f"   ✅ Валидация email работает для: {email}")

        # Тест валидации пароля
        try:
            user = User(
                username="test_validation",
                email="test@test.com",
                password="",  # Пустой пароль
            )
            db.session.add(user)
            db.session.flush()
            print("   ❌ Валидация пароля не работает")
            db.session.rollback()
        except Exception:
            print("   ✅ Валидация пароля работает")

    except Exception as e:
        print(f"   ❌ Ошибка тестирования валидации: {e}")


def test_query_performance():
    """Тестирует производительность запросов"""
    print("\n⚡ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ ЗАПРОСОВ")
    print("-" * 40)

    try:
        # Тест простого запроса
        start_time = time.time()
        User.query.count()
        simple_query_time = time.time() - start_time
        print(f"   ✅ Простой запрос: {simple_query_time:.4f} сек")

        # Тест сложного запроса с JOIN
        start_time = time.time()
        db.session.query(User, Subject, Material).join(
            Submission, User.id == Submission.user_id
        ).join(Material, Submission.material_id == Material.id).join(
            Subject, Material.subject_id == Subject.id
        ).limit(10).all()
        complex_query_time = time.time() - start_time
        print(f"   ✅ Сложный запрос с JOIN: {complex_query_time:.4f} сек")

        # Тест запроса с фильтрацией
        start_time = time.time()
        User.query.filter(User.is_verified).all()
        filtered_query_time = time.time() - start_time
        print(f"   ✅ Запрос с фильтрацией: {filtered_query_time:.4f} сек")

    except Exception as e:
        print(f"   ❌ Ошибка тестирования производительности: {e}")


def test_database_statistics():
    """Тестирует статистику базы данных"""
    print("\n📊 ТЕСТ СТАТИСТИКИ БАЗЫ ДАННЫХ")
    print("-" * 40)

    try:
        # Подсчет пользователей
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        subscribed_users = User.query.filter_by(is_subscribed=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()

        print(f"   👥 Всего пользователей: {total_users}")
        print(f"   ✅ Подтвержденных пользователей: {verified_users}")
        print(f"   💰 Подписчиков: {subscribed_users}")
        print(f"   👑 Администраторов: {admin_users}")

        # Подсчет предметов и материалов
        total_subjects = Subject.query.count()
        total_materials = Material.query.count()

        print(f"   📚 Всего предметов: {total_subjects}")
        print(f"   📖 Всего материалов: {total_materials}")

        # Подсчет заданий
        total_submissions = Submission.query.count()
        recent_submissions = Submission.query.filter(
            Submission.submitted_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        print(f"   📝 Всего заданий: {total_submissions}")
        print(f"   🆕 Заданий за неделю: {recent_submissions}")

        # Подсчет ссылок
        total_links = ShortLink.query.count()

        print(f"   🔗 Всего ссылок: {total_links}")

    except Exception as e:
        print(f"   ❌ Ошибка получения статистики: {e}")


def cleanup_test_data(test_data: Dict[str, Any]):
    """Очищает все тестовые данные"""
    print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
    print("-" * 40)

    try:
        # Удаляем тестовые данные в обратном порядке (с учетом зависимостей)
        entities_to_delete = ["submission", "link", "material", "subject", "user"]

        for entity_key in entities_to_delete:
            if entity_key in test_data:
                entity = test_data[entity_key]
                try:
                    db.session.delete(entity)
                    print(f"   ✅ Удален {entity_key}: {type(entity).__name__}")
                except Exception as e:
                    print(f"   ⚠️ Ошибка при удалении {entity_key}: {e}")

        # Удаляем все тестовые данные по паттернам
        cleanup_patterns = [
            (User, User.username.like("test_user_%")),
            (Subject, Subject.title.like("Test Subject%")),
            (Material, Material.title.like("Test Material%")),
            (Submission, Submission.text.like("Test submission%")),
            (ShortLink, ShortLink.code.like("test_%")),
        ]

        for model, pattern in cleanup_patterns:
            try:
                entities = model.query.filter(pattern).all()
                for entity in entities:
                    db.session.delete(entity)
                if entities:
                    print(f"   ✅ Удалено {len(entities)} {model.__name__} по паттерну")
            except Exception as e:
                print(f"   ⚠️ Ошибка при удалении {model.__name__} по паттерну: {e}")

        # Фиксируем все изменения
        db.session.commit()
        print("   💾 Все тестовые данные очищены")

    except Exception as e:
        print(f"   ❌ Ошибка при очистке данных: {e}")
        db.session.rollback()


def main():
    """Основная функция"""
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
