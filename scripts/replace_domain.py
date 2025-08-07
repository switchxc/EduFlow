#!/usr/bin/env python3
"""
Скрипт для замены всех упоминаний cysu.ru на cysu.ru
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def find_files_with_domain(project_root: str, include_logs: bool = False) -> List[Tuple[str, List[int]]]:
    """
    Находит все файлы, содержащие упоминания cysu.ru
    """
    files_with_domain = []
    domain_pattern = re.compile(r'ck7project\.online')
    
    for root, dirs, files in os.walk(project_root):
        # Пропускаем .git и другие служебные директории
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            # Пропускаем бинарные файлы
            if file.endswith(('.pyc', '.pyo', '.db', '.sqlite', '.sqlite3')):
                continue
            
            # Пропускаем логи если не включена опция
            if not include_logs and file.endswith('.log'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = list(domain_pattern.finditer(content))
                    if matches:
                        line_numbers = []
                        lines = content.split('\n')
                        for match in matches:
                            # Находим номер строки для каждого совпадения
                            pos = match.start()
                            line_num = content[:pos].count('\n') + 1
                            line_numbers.append(line_num)
                        files_with_domain.append((file_path, line_numbers))
            except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                continue
    
    return files_with_domain

def replace_domain_in_file(file_path: str) -> int:
    """
    Заменяет все упоминания cysu.ru на cysu.ru в файле
    Возвращает количество замен
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Подсчитываем количество замен
        original_count = len(re.findall(r'ck7project\.online', content))
        
        if original_count == 0:
            return 0
        
        # Выполняем замену
        new_content = re.sub(r'ck7project\.online', 'cysu.ru', content)
        
        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return original_count
        
    except (UnicodeDecodeError, PermissionError, FileNotFoundError) as e:
        print(f"Ошибка при обработке файла {file_path}: {e}")
        return 0

def clear_logs(project_root: str) -> int:
    """
    Очищает все лог-файлы от упоминаний старого домена
    """
    cleared_files = 0
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Проверяем наличие старого домена
                    if 'cysu.ru' in content:
                        # Очищаем файл
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('')
                        cleared_files += 1
                        print(f"   🧹 Очищен лог: {os.path.relpath(file_path, project_root)}")
                        
                except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                    continue
    
    return cleared_files

def main():
    """
    Основная функция скрипта
    """
    parser = argparse.ArgumentParser(description='Замена домена cysu.ru на cysu.ru')
    parser.add_argument('--clear-logs', action='store_true', 
                       help='Очистить лог-файлы от старых записей')
    parser.add_argument('--include-logs', action='store_true',
                       help='Включить лог-файлы в поиск и замену')
    
    args = parser.parse_args()
    
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("🔍 Поиск файлов с упоминаниями cysu.ru...")
    
    # Находим файлы с упоминаниями домена
    files_with_domain = find_files_with_domain(str(project_root), args.include_logs)
    
    if not files_with_domain:
        print("✅ Упоминания cysu.ru не найдены")
    else:
        print(f"📁 Найдено {len(files_with_domain)} файлов с упоминаниями домена:")
        for file_path, line_numbers in files_with_domain:
            relative_path = os.path.relpath(file_path, project_root)
            print(f"   📄 {relative_path} (строки: {', '.join(map(str, line_numbers))})")
        
        print("\n🔄 Начинаю замену...")
        
        total_replacements = 0
        processed_files = 0
        
        for file_path, _ in files_with_domain:
            replacements = replace_domain_in_file(file_path)
            if replacements > 0:
                relative_path = os.path.relpath(file_path, project_root)
                print(f"   ✅ {relative_path}: {replacements} замен")
                total_replacements += replacements
                processed_files += 1
        
        print(f"\n🎉 Замена завершена!")
        print(f"   📊 Обработано файлов: {processed_files}")
        print(f"   🔄 Всего замен: {total_replacements}")
        print(f"   🏠 Новый домен: cysu.ru")
    
    # Очистка логов если запрошено
    if args.clear_logs:
        print("\n🧹 Очистка лог-файлов...")
        cleared_files = clear_logs(str(project_root))
        if cleared_files > 0:
            print(f"   ✅ Очищено лог-файлов: {cleared_files}")
        else:
            print("   ℹ️ Лог-файлы для очистки не найдены")

if __name__ == "__main__":
    main()
