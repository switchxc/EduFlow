#!/usr/bin/env python3
"""
Скрипт для очистки всех тикетов из базы данных cysu

Использование:
    python clear_tickets.py

Внимание: Этот скрипт удалит ВСЕ тикеты из базы данных без возможности восстановления!
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Проверяем, что модуль app существует
try:
    from app import create_app, db
    from app.models import Ticket, TicketFile, TicketMessage
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"📁 Текущая директория: {os.getcwd()}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Python path: {sys.path}")
    sys.exit(1)


def clear_all_tickets() -> None:
    """
    Удаляет все тикеты и связанные с ними данные из базы данных
    
    Удаляет:
    - Все тикеты (Ticket)
    - Все файлы тикетов (TicketFile) 
    - Все сообщения тикетов (TicketMessage)
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Получаем количество записей для отчета
            tickets_count = Ticket.query.count()
            files_count = TicketFile.query.count()
            messages_count = TicketMessage.query.count()
            
            print(f"📊 Найдено записей для удаления:")
            print(f"   - Тикетов: {tickets_count}")
            print(f"   - Файлов тикетов: {files_count}")
            print(f"   - Сообщений тикетов: {messages_count}")
            
            if tickets_count == 0:
                print("✅ База данных уже пуста - тикетов для удаления нет")
                return
            
            # Запрашиваем подтверждение
            print("\n⚠️  ВНИМАНИЕ: Это действие необратимо!")
            confirm = input("Введите 'YES' для подтверждения удаления всех тикетов: ")
            
            if confirm != 'YES':
                print("❌ Операция отменена пользователем")
                return
            
            # Удаляем все записи
            print("\n🗑️  Удаляем тикеты...")
            
            # Удаляем сообщения тикетов
            TicketMessage.query.delete()
            print("   ✅ Сообщения тикетов удалены")
            
            # Удаляем файлы тикетов
            TicketFile.query.delete()
            print("   ✅ Файлы тикетов удалены")
            
            # Удаляем сами тикеты
            Ticket.query.delete()
            print("   ✅ Тикеты удалены")
            
            # Фиксируем изменения
            db.session.commit()
            print("\n✅ Все тикеты успешно удалены из базы данных!")
            
            # Проверяем результат
            remaining_tickets = Ticket.query.count()
            remaining_files = TicketFile.query.count()
            remaining_messages = TicketMessage.query.count()
            
            print(f"\n📊 Результат:")
            print(f"   - Осталось тикетов: {remaining_tickets}")
            print(f"   - Осталось файлов: {remaining_files}")
            print(f"   - Осталось сообщений: {remaining_messages}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при удалении тикетов: {e}")
            sys.exit(1)


def clear_ticket_files_from_disk() -> None:
    """
    Удаляет физические файлы тикетов с диска
    
    Внимание: Эта функция удаляет файлы из папки app/static/ticket_files/
    """
    ticket_files_dir = project_root / "app" / "static" / "ticket_files"
    
    if not ticket_files_dir.exists():
        print("📁 Папка с файлами тикетов не найдена")
        return
    
    try:
        files_count = len(list(ticket_files_dir.glob("*")))
        
        if files_count == 0:
            print("📁 Папка с файлами тикетов пуста")
            return
        
        print(f"\n📁 Найдено файлов в папке ticket_files: {files_count}")
        
        confirm = input("Удалить физические файлы тикетов с диска? (YES/NO): ")
        
        if confirm != 'YES':
            print("❌ Удаление файлов отменено")
            return
        
        # Удаляем все файлы в папке
        deleted_count = 0
        for file_path in ticket_files_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
        
        print(f"✅ Удалено {deleted_count} файлов с диска")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении файлов: {e}")


def main() -> None:
    """Главная функция скрипта"""
    print("🧹 Скрипт очистки тикетов cysu")
    print("=" * 50)
    
    # Очищаем базу данных
    clear_all_tickets()
    
    # Предлагаем очистить файлы с диска
    print("\n" + "=" * 50)
    clear_ticket_files_from_disk()
    
    print("\n🎉 Очистка завершена!")


if __name__ == "__main__":
    main() 