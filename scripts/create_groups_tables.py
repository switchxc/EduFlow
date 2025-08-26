#!/usr/bin/env python3
"""
Скрипт для создания таблиц групп в базе данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Group, SubjectGroup

def create_groups_tables():
    """Создает таблицы для системы групп"""
    app = create_app()
    
    with app.app_context():
        print("Создание таблиц для системы групп...")
        
        # Создаем таблицы
        db.create_all()
        
        print("✅ Таблицы созданы успешно!")
        
        # Проверяем, есть ли уже группы
        existing_groups = Group.query.count()
        if existing_groups == 0:
            print("Создание базовых групп...")
            
            # Создаем несколько базовых групп
            groups_data = [
                {
                    'name': 'ИСП-11',
                    'description': 'Группа для студентов ИСП-11',
                    'is_active': True
                },
            ]
            
            for group_data in groups_data:
                group = Group(**group_data)
                db.session.add(group)
                print(f"  - Создана группа: {group.name}")
            
            db.session.commit()
            print("✅ Базовые группы созданы!")
        else:
            print(f"Найдено существующих групп: {existing_groups}")
        
        print("\n🎉 Миграция завершена успешно!")

if __name__ == '__main__':
    create_groups_tables()
