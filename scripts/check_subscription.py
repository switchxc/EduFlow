# cysu v1.5.0 - Тестирование сайта
#!/usr/bin/env python3
"""
Скрипт для проверки подписки пользователя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import create_app, db
from app.models import User

def check_subscription(username):
    """Проверяет подписку пользователя"""
    app = create_app()
    
    with app.app_context():
        # Ищем пользователя по нику
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ Пользователь с ником '{username}' не найден")
            return False
        
        print(f"👤 Пользователь: {user.username} (ID: {user.id})")
        print(f"📧 Email: {user.email}")
        print(f"👑 Администратор: {'Да' if user.is_admin else 'Нет'}")
        print(f"✅ Подтвержден: {'Да' if user.is_verified else 'Нет'}")
        print("-" * 40)
        
        # Проверяем подписку
        if user.is_subscribed:
            print("🎫 Статус подписки: АКТИВНА")
            
            if user.subscription_expires:
                now = datetime.utcnow()
                days_left = (user.subscription_expires - now).days
                
                print(f"📅 Дата окончания: {user.subscription_expires.strftime('%d.%m.%Y %H:%M:%S')}")
                print(f"⏰ Осталось дней: {days_left}")
                
                if days_left > 0:
                    print("✅ Подписка действительна")
                else:
                    print("❌ Подписка истекла")
            else:
                print("📅 Дата окончания: БЕЗ ОГРАНИЧЕНИЙ")
                print("✅ Подписка действительна")
            
            if user.is_manual_subscription:
                print("🔧 Тип: Выдана вручную администратором")
            else:
                print("💳 Тип: Оплачена через ЮKassa")
        else:
            print("🎫 Статус подписки: НЕАКТИВНА")
            print("❌ Пользователь не имеет подписки")
        
        return True

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python3 scripts/check_subscription.py <username>")
        print("Пример: python3 scripts/check_subscription.py john_doe")
        sys.exit(1)
    
    username = sys.argv[1]
    
    print(f"🔍 Проверка подписки пользователя: {username}")
    print("=" * 50)
    
    success = check_subscription(username)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
