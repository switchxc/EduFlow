#!/usr/bin/env python3
"""
Утилиты для тестирования cysu

Содержит общие функции для всех тестовых скриптов:
- Очистка тестовых данных
- Создание тестовых данных
- Общие проверки
"""

import sys
import os
from pathlib import Path
from typing import List, Any

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models import User, Subject, Material, Submission, Payment, ChatMessage, Ticket
from datetime import datetime


def global_cleanup() -> None:
    """Глобальная очистка всех тестовых данных"""
    app = create_app()
    
    with app.app_context():
        print("🧹 ГЛОБАЛЬНАЯ ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 60)
        
        try:
            # 1. Очистка тестовых пользователей
            cleanup_test_users()
            
            # 2. Очистка тестовых предметов
            cleanup_test_subjects()
            
            # 3. Очистка тестовых материалов
            cleanup_test_materials()
            
            # 4. Очистка orphaned записей
            cleanup_orphaned_records()
            
            # 5. Очистка временных файлов
            cleanup_temp_files()
            
            db.session.commit()
            print("   ✅ Глобальная очистка завершена успешно!")
            
        except Exception as e:
            print(f"   ❌ Ошибка при глобальной очистке: {e}")
            db.session.rollback()


def cleanup_test_users() -> None:
    """Очищает всех тестовых пользователей"""
    try:
        # Паттерны для тестовых пользователей
        test_patterns = [
            'test_%',
            'hacker_test_%',
            'test_user_%',
            'test_security_%',
            'test_payment_%',
            'test_site_%'
        ]
        
        total_deleted = 0
        
        for pattern in test_patterns:
            users = User.query.filter(User.username.like(pattern)).all()
            for user in users:
                try:
                    # Удаляем связанные данные
                    Payment.query.filter_by(user_id=user.id).delete()
                    Submission.query.filter_by(user_id=user.id).delete()
                    ChatMessage.query.filter_by(user_id=user.id).delete()
                    Ticket.query.filter_by(user_id=user.id).delete()
                    
                    db.session.delete(user)
                    total_deleted += 1
                except Exception as e:
                    print(f"      ⚠️ Ошибка при удалении пользователя {user.username}: {e}")
        
        # Удаляем пользователей с тестовыми email
        test_email_users = User.query.filter(User.email.like('%@test.com')).all()
        for user in test_email_users:
            try:
                Payment.query.filter_by(user_id=user.id).delete()
                Submission.query.filter_by(user_id=user.id).delete()
                ChatMessage.query.filter_by(user_id=user.id).delete()
                Ticket.query.filter_by(user_id=user.id).delete()
                
                db.session.delete(user)
                total_deleted += 1
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении пользователя с email {user.email}: {e}")
        
        if total_deleted > 0:
            print(f"   👥 Удалено тестовых пользователей: {total_deleted}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке пользователей: {e}")


def cleanup_test_subjects() -> None:
    """Очищает тестовые предметы"""
    try:
        # Паттерны для тестовых предметов
        test_patterns = [
            'Test%',
            'Test Subject%',
            'Тестовый%'
        ]
        
        total_deleted = 0
        
        for pattern in test_patterns:
            subjects = Subject.query.filter(Subject.title.like(pattern)).all()
            for subject in subjects:
                try:
                    # Удаляем связанные материалы
                    Material.query.filter_by(subject_id=subject.id).delete()
                    db.session.delete(subject)
                    total_deleted += 1
                except Exception as e:
                    print(f"      ⚠️ Ошибка при удалении предмета {subject.title}: {e}")
        
        if total_deleted > 0:
            print(f"   📚 Удалено тестовых предметов: {total_deleted}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке предметов: {e}")


def cleanup_test_materials() -> None:
    """Очищает тестовые материалы"""
    try:
        # Паттерны для тестовых материалов
        test_patterns = [
            'Test%',
            'Test Material%',
            'Тестовый%'
        ]
        
        total_deleted = 0
        
        for pattern in test_patterns:
            materials = Material.query.filter(Material.title.like(pattern)).all()
            for material in materials:
                try:
                    db.session.delete(material)
                    total_deleted += 1
                except Exception as e:
                    print(f"      ⚠️ Ошибка при удалении материала {material.title}: {e}")
        
        if total_deleted > 0:
            print(f"   📄 Удалено тестовых материалов: {total_deleted}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке материалов: {e}")


def cleanup_orphaned_records() -> None:
    """Удаляет записи без связанных пользователей"""
    try:
        # Получаем список всех пользователей
        user_ids = [u.id for u in User.query.all()]
        
        # Удаляем orphaned записи
        orphaned_payments = Payment.query.filter(~Payment.user_id.in_(user_ids)).all()
        orphaned_submissions = Submission.query.filter(~Submission.user_id.in_(user_ids)).all()
        orphaned_messages = ChatMessage.query.filter(~ChatMessage.user_id.in_(user_ids)).all()
        orphaned_tickets = Ticket.query.filter(~Ticket.user_id.in_(user_ids)).all()
        
        # Удаляем платежи
        for payment in orphaned_payments:
            try:
                db.session.delete(payment)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении orphaned платежа {payment.id}: {e}")
        
        # Удаляем решения
        for submission in orphaned_submissions:
            try:
                db.session.delete(submission)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении orphaned решения {submission.id}: {e}")
        
        # Удаляем сообщения
        for message in orphaned_messages:
            try:
                db.session.delete(message)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении orphaned сообщения {message.id}: {e}")
        
        # Удаляем тикеты
        for ticket in orphaned_tickets:
            try:
                db.session.delete(ticket)
            except Exception as e:
                print(f"      ⚠️ Ошибка при удалении orphaned тикета {ticket.id}: {e}")
        
        total_orphaned = len(orphaned_payments) + len(orphaned_submissions) + len(orphaned_messages) + len(orphaned_tickets)
        
        if total_orphaned > 0:
            print(f"   🧹 Удалено orphaned записей: {total_orphaned}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке orphaned записей: {e}")


def cleanup_temp_files() -> None:
    """Очищает временные файлы"""
    try:
        # Папки для проверки
        temp_folders = [
            "app/static/uploads",
            "app/static/chat_files",
            "app/static/ticket_files"
        ]
        
        total_files = 0
        
        for folder_path in temp_folders:
            folder = Path(folder_path)
            if folder.exists():
                # Удаляем файлы старше 1 часа
                current_time = datetime.now()
                for file_path in folder.glob("*"):
                    if file_path.is_file():
                        try:
                            file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_age.total_seconds() > 3600:  # 1 час
                                file_path.unlink()
                                total_files += 1
                        except Exception as e:
                            print(f"      ⚠️ Ошибка при удалении файла {file_path}: {e}")
        
        if total_files > 0:
            print(f"   📁 Удалено временных файлов: {total_files}")
        
    except Exception as e:
        print(f"   ❌ Ошибка при очистке временных файлов: {e}")


def get_test_statistics() -> dict:
    """Получает статистику тестовых данных"""
    app = create_app()
    
    with app.app_context():
        stats = {
            'test_users': User.query.filter(User.username.like('test_%')).count(),
            'test_subjects': Subject.query.filter(Subject.title.like('Test%')).count(),
            'test_materials': Material.query.filter(Material.title.like('Test%')).count(),
            'total_payments': Payment.query.count(),
            'total_submissions': Submission.query.count(),
            'total_messages': ChatMessage.query.count(),
            'total_tickets': Ticket.query.count()
        }
        
        return stats


if __name__ == '__main__':
    # Если скрипт запущен напрямую, выполняем глобальную очистку
    global_cleanup()
