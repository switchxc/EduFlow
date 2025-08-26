#!/usr/bin/env python3
"""
Скрипт для добавления колонки group_id в таблицу user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def add_group_id_column():
    """Добавляет колонку group_id в таблицу user"""
    app = create_app()
    
    with app.app_context():
        print("Добавление колонки group_id в таблицу user...")
        
        try:
            # Проверяем, существует ли уже колонка group_id
            from sqlalchemy import text
            result = db.session.execute(text("PRAGMA table_info(user)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'group_id' in columns:
                print("✅ Колонка group_id уже существует")
                return
            
            # Добавляем колонку group_id
            db.session.execute(text("ALTER TABLE user ADD COLUMN group_id INTEGER"))
            db.session.commit()
            
            print("✅ Колонка group_id успешно добавлена!")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            db.session.rollback()
            return
        
        print("\n🎉 Миграция завершена успешно!")

if __name__ == '__main__':
    add_group_id_column()
