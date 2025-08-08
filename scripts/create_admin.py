import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Subject, Material, Submission, Ticket, TicketMessage, Notification, Payment, PasswordReset, EmailVerification, ChatMessage, TicketFile
from werkzeug.security import generate_password_hash

def init_database():
    """Инициализация базы данных"""
    import sqlite3
    
    # Создаем базу данных в корне проекта
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(project_root, 'app.db')
    
    print(f"Создание базы данных: {db_file}")
    
    # Создаем пустую базу данных если её нет
    if not os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        conn.close()
        print("✅ Файл базы данных создан")
    
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        print("Создание таблиц базы данных...")
        db.create_all()
        print("✅ Таблицы базы данных созданы")
        
        # Создаем администратора по умолчанию
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='support@cysu.ru',
                password=generate_password_hash('admin123'),
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Администратор создан")
        else:
            print("✅ Администратор уже существует")
        
        print("✅ База данных инициализирована успешно!")

if __name__ == '__main__':
    init_database() 