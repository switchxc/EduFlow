# cysu v1.5.0 - Тестирование сайта
#!/usr/bin/env python3
"""
Скрипт для выдачи подписки до 99 года по нику пользователя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app import create_app, db
from app.models import User

def grant_subscription(username):
    """Выдает подписку пользователю до 99 года"""
    app = create_app()
    
    with app.app_context():
        # Ищем пользователя по нику
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ Пользователь с ником '{username}' не найден")
            return False
        
        print(f"Найден пользователь: {user.username} (ID: {user.id})")
        print(f"Email: {user.email}")
        print(f"Текущий статус подписки: {'Активна' if user.is_subscribed else 'Неактивна'}")
        
        if user.subscription_expires:
            print(f"Текущая дата окончания: {user.subscription_expires.strftime('%d.%m.%Y')}")
        
        # Устанавливаем подписку до 99 года (2099-12-31)
        subscription_end = datetime(2099, 12, 31, 23, 59, 59)
        
        user.is_subscribed = True
        user.subscription_expires = subscription_end
        user.is_manual_subscription = True  # Подписка выдана вручную
        
        db.session.commit()
        
        print(f"✅ Подписка выдана пользователю {user.username}")
        print(f"📅 Дата окончания: {subscription_end.strftime('%d.%m.%Y')}")
        print(f"⏰ Время окончания: {subscription_end.strftime('%H:%M:%S')}")
        
        return True

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python3 scripts/grant_subscription.py <username>")
        print("Пример: python3 scripts/grant_subscription.py john_doe")
        sys.exit(1)
    
    username = sys.argv[1]
    
    print(f"🎯 Выдача подписки пользователю: {username}")
    print("=" * 50)
    
    success = grant_subscription(username)
    
    if success:
        print("=" * 50)
        print("✅ Операция завершена успешно!")
    else:
        print("=" * 50)
        print("❌ Операция завершена с ошибкой!")
        sys.exit(1)

if __name__ == '__main__':
    main()
