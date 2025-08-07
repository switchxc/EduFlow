"""
Утилиты для работы с улучшенной системой хранения файлов
"""

import os
import shutil
from datetime import datetime
from typing import Tuple, List
from flask import current_app


class FileStorageManager:
    """
    Менеджер для работы с файловой системой хранения
    """

    # Разрешенные расширения файлов
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "rtf", "odt"}
    ALLOWED_ARCHIVE_EXTENSIONS = {"zip", "rar", "7z", "tar", "gz"}
    ALLOWED_TICKET_EXTENSIONS = (
        ALLOWED_IMAGE_EXTENSIONS
        | ALLOWED_DOCUMENT_EXTENSIONS
        | ALLOWED_ARCHIVE_EXTENSIONS
    )

    # Максимальные размеры файлов (в байтах)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB для изображений

    @staticmethod
    def get_subject_upload_path(
        subject_id: int, user_id: int, filename: str
    ) -> Tuple[str, str]:
        """
        Создает путь для загрузки файлов решений пользователей по предметам

        Args:
            subject_id: ID предмета
            user_id: ID пользователя
            filename: Имя файла

        Returns:
            Tuple[str, str]: (полный путь к файлу, относительный путь для БД)
        """
        # Создаем структуру папок: uploads/id_предмета/id_пользователя/
        upload_base = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
        subject_path = os.path.join(upload_base, str(subject_id), str(user_id))

        # Создаем папки если их нет
        os.makedirs(subject_path, exist_ok=True)

        # Полный путь к файлу
        full_path = os.path.join(subject_path, filename)

        # Относительный путь для БД: id_предмета/id_пользователя/файл
        relative_path = os.path.join(str(subject_id), str(user_id), filename)

        return full_path, relative_path

    @staticmethod
    def get_material_upload_path(subject_id: int, filename: str) -> Tuple[str, str]:
        """
        Создает путь для загрузки файлов материалов (заданий) по предметам

        Args:
            subject_id: ID предмета
            filename: Имя файла

        Returns:
            Tuple[str, str]: (полный путь к файлу, относительный путь для БД)
        """
        # Создаем структуру папок: uploads/id_предмета/
        upload_base = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
        subject_path = os.path.join(upload_base, str(subject_id))

        # Создаем папки если их нет
        os.makedirs(subject_path, exist_ok=True)

        # Полный путь к файлу
        full_path = os.path.join(subject_path, filename)

        # Относительный путь для БД: id_предмета/файл
        relative_path = os.path.join(str(subject_id), filename)

        return full_path, relative_path

    @staticmethod
    def get_chat_file_path(user_id: int, filename: str) -> Tuple[str, str]:
        """
        Создает путь для загрузки файлов чата

        Args:
            user_id: ID пользователя
            filename: Имя файла

        Returns:
            Tuple[str, str]: (полный путь к файлу, относительный путь для БД)
        """
        # Создаем структуру папок: chat_files/пользователь/
        chat_base = current_app.config.get("CHAT_FILES_FOLDER", "app/static/chat_files")
        user_path = os.path.join(chat_base, str(user_id))

        # Создаем папку пользователя если её нет
        os.makedirs(user_path, exist_ok=True)

        # Генерируем уникальное имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{timestamp}_{name}{ext}"

        # Полный путь к файлу
        full_path = os.path.join(user_path, unique_filename)

        # Относительный путь для БД: пользователь/файл
        relative_path = os.path.join(str(user_id), unique_filename)

        return full_path, relative_path

    @staticmethod
    def get_ticket_file_path(ticket_id: int, filename: str) -> Tuple[str, str]:
        """
        Создает путь для загрузки файлов тикетов

        Args:
            ticket_id: ID тикета
            filename: Имя файла

        Returns:
            Tuple[str, str]: (полный путь к файлу, относительный путь для БД)
        """
        # Создаем структуру папок: ticket_files/номер_тикета/
        ticket_base = current_app.config.get(
            "TICKET_FILES_FOLDER", "app/static/ticket_files"
        )
        ticket_path = os.path.join(ticket_base, str(ticket_id))

        # Создаем папку тикета если её нет
        os.makedirs(ticket_path, exist_ok=True)

        # Генерируем уникальное имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{timestamp}_{name}{ext}"

        # Полный путь к файлу
        full_path = os.path.join(ticket_path, unique_filename)

        # Относительный путь для БД: номер_тикета/файл
        relative_path = os.path.join(str(ticket_id), unique_filename)

        return full_path, relative_path

    @staticmethod
    def save_file(file, full_path: str) -> bool:
        """
        Сохраняет файл по указанному пути

        Args:
            file: Файловый объект
            full_path: Полный путь для сохранения

        Returns:
            bool: True если файл сохранен успешно
        """
        try:
            file.save(full_path)
            return True
        except Exception as e:
            current_app.logger.error(f"Ошибка сохранения файла {full_path}: {str(e)}")
            return False

    @staticmethod
    def delete_file(relative_path: str) -> bool:
        """
        Удаляет файл по относительному пути

        Args:
            relative_path: Относительный путь к файлу

        Returns:
            bool: True если файл удален успешно
        """
        try:
            # Получаем полный путь к файлу
            static_folder = current_app.static_folder
            full_path = os.path.join(static_folder, relative_path)

            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Ошибка удаления файла {relative_path}: {str(e)}")
            return False

    @staticmethod
    def delete_ticket_files(ticket_id: int) -> bool:
        """
        Удаляет все файлы тикета

        Args:
            ticket_id: ID тикета

        Returns:
            bool: True если файлы удалены успешно
        """
        try:
            ticket_base = current_app.config.get(
                "TICKET_FILES_FOLDER", "app/static/ticket_files"
            )
            ticket_path = os.path.join(ticket_base, str(ticket_id))

            if os.path.exists(ticket_path):
                shutil.rmtree(ticket_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(
                f"Ошибка удаления файлов тикета {ticket_id}: {str(e)}"
            )
            return False

    @staticmethod
    def delete_user_files(user_id: int) -> bool:
        """
        Удаляет все файлы пользователя (чаты, материалы)

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если файлы удалены успешно
        """
        try:
            # Удаляем файлы чата
            chat_base = current_app.config.get(
                "CHAT_FILES_FOLDER", "app/static/chat_files"
            )
            chat_path = os.path.join(chat_base, str(user_id))
            if os.path.exists(chat_path):
                shutil.rmtree(chat_path)

            # Удаляем файлы материалов
            upload_base = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
            if os.path.exists(upload_base):
                for subject_folder in os.listdir(upload_base):
                    user_path = os.path.join(upload_base, subject_folder, str(user_id))
                    if os.path.exists(user_path):
                        shutil.rmtree(user_path)

            return True
        except Exception as e:
            current_app.logger.error(
                f"Ошибка удаления файлов пользователя {user_id}: {str(e)}"
            )
            return False

    @staticmethod
    def get_file_type(filename: str) -> str:
        """
        Определяет тип файла по расширению

        Args:
            filename: Имя файла

        Returns:
            str: Тип файла (image, document, archive, unknown)
        """
        if not filename or "." not in filename:
            return "unknown"

        extension = filename.rsplit(".", 1)[1].lower()

        if extension in FileStorageManager.ALLOWED_IMAGE_EXTENSIONS:
            return "image"
        elif extension in FileStorageManager.ALLOWED_DOCUMENT_EXTENSIONS:
            return "document"
        elif extension in FileStorageManager.ALLOWED_ARCHIVE_EXTENSIONS:
            return "archive"
        else:
            return "unknown"

    @staticmethod
    def is_allowed_file(filename: str, allowed_extensions: set = None) -> bool:
        """
        Проверяет, разрешен ли файл для загрузки

        Args:
            filename: Имя файла
            allowed_extensions: Множество разрешенных расширений (по умолчанию ALLOWED_TICKET_EXTENSIONS)

        Returns:
            bool: True если файл разрешен
        """
        if not filename or "." not in filename:
            return False

        if allowed_extensions is None:
            allowed_extensions = FileStorageManager.ALLOWED_TICKET_EXTENSIONS

        extension = filename.rsplit(".", 1)[1].lower()
        return extension in allowed_extensions

    @staticmethod
    def validate_file_size(file, max_size: int = None) -> bool:
        """
        Проверяет размер файла

        Args:
            file: Файловый объект
            max_size: Максимальный размер в байтах (по умолчанию MAX_FILE_SIZE)

        Returns:
            bool: True если размер файла допустим
        """
        if max_size is None:
            max_size = FileStorageManager.MAX_FILE_SIZE

        file_size = FileStorageManager.get_file_size(file)
        return file_size <= max_size

    @staticmethod
    def get_file_size(file) -> int:
        """
        Получает размер файла в байтах

        Args:
            file: Файловый объект

        Returns:
            int: Размер файла в байтах
        """
        try:
            # Сохраняем текущую позицию
            current_pos = file.tell()

            # Перемещаемся в конец файла
            file.seek(0, 2)
            size = file.tell()

            # Возвращаемся в исходную позицию
            file.seek(current_pos)

            return size
        except Exception:
            return 0

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Форматирует размер файла в читаемый вид

        Args:
            size_bytes: Размер в байтах

        Returns:
            str: Отформатированный размер (например, "1.5 MB")
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    @staticmethod
    def process_ticket_files(files: List, ticket_id: int) -> List[dict]:
        """
        Обрабатывает файлы тикета и возвращает информацию о сохраненных файлах

        Args:
            files: Список файловых объектов
            ticket_id: ID тикета

        Returns:
            List[dict]: Список словарей с информацией о файлах
        """
        saved_files = []

        for file in files:
            if not file or not file.filename or not file.filename.strip():
                continue

            # Проверяем размер файла
            if not FileStorageManager.validate_file_size(file):
                current_app.logger.warning(f"Файл {file.filename} слишком большой")
                continue

            # Проверяем расширение файла
            if not FileStorageManager.is_allowed_file(file.filename):
                current_app.logger.warning(
                    f"Неподдерживаемый тип файла: {file.filename}"
                )
                continue

            # Получаем пути для сохранения
            full_path, relative_path = FileStorageManager.get_ticket_file_path(
                ticket_id, file.filename
            )

            # Сохраняем файл
            if FileStorageManager.save_file(file, full_path):
                file_info = {
                    "file_path": relative_path,
                    "file_name": file.filename,
                    "file_size": FileStorageManager.get_file_size(file),
                    "file_type": FileStorageManager.get_file_type(file.filename),
                }
                saved_files.append(file_info)
                current_app.logger.info(
                    f"Файл {file.filename} сохранен для тикета {ticket_id}"
                )
            else:
                current_app.logger.error(f"Ошибка сохранения файла {file.filename}")

        return saved_files
