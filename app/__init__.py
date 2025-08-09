from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import logging
import os

# Загружаем переменные окружения
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, instance_path=None)
    
    # Конфигурация из переменных окружения
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    # Конфигурация базы данных - создаем в корне проекта
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Диагностика базы данных
    if not app.debug and not app.testing:
        app.logger.info(f'Database path: {db_path}')
        app.logger.info(f'Database exists: {os.path.exists(db_path)}')
        app.logger.info(f'Database readable: {os.access(db_path, os.R_OK)}')
        app.logger.info(f'Database writable: {os.access(db_path, os.W_OK)}')
    
    # Конфигурация загрузки файлов
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    app.config['CHAT_FILES_FOLDER'] = os.getenv('CHAT_FILES_FOLDER', 'app/static/chat_files')
    app.config['TICKET_FILES_FOLDER'] = os.getenv('TICKET_FILES_FOLDER', 'app/static/ticket_files')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 20 * 1024 * 1024))
    
    # Конфигурация почты
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-password')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')
    
    # Конфигурация платежей
    app.config['YOOKASSA_SHOP_ID'] = os.getenv('YOOKASSA_SHOP_ID', 'your-shop-id')
    app.config['YOOKASSA_SECRET_KEY'] = os.getenv('YOOKASHA_SECRET_KEY', 'your-secret-key')
    app.config['YOOKASSA_TEST_MODE'] = os.getenv('YOOKASSA_TEST_MODE', 'True').lower() == 'true'
    
    # Цены подписки
    app.config['SUBSCRIPTION_PRICES'] = {
        '1': float(os.getenv('SUBSCRIPTION_PRICE_1', 89.00)),
        '3': float(os.getenv('SUBSCRIPTION_PRICE_3', 199.00)),
        '6': float(os.getenv('SUBSCRIPTION_PRICE_6', 349.00)),
        '12': float(os.getenv('SUBSCRIPTION_PRICE_12', 469.00))
    }
    app.config['SUBSCRIPTION_CURRENCY'] = os.getenv('SUBSCRIPTION_CURRENCY', 'RUB')
    
    # Настройки логирования
    app.config['LOG_FILE'] = os.getenv('LOG_FILE', 'err.log')
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    
    # Настройка логирования
    if not app.debug and not app.testing:
        # Создаем директорию для логов если её нет
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Настраиваем файловый обработчик
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        # Настраиваем формат логов
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру приложения
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        app.logger.info('Приложение запущено')
    
    db.init_app(app)
    
    # Проверка подключения к базе данных
    try:
        with app.app_context():
            db.engine.connect()
            if not app.debug and not app.testing:
                app.logger.info('Database connection successful')
            # Обеспечиваем наличие таблиц (в том числе для ShortLink)
            try:
                db.create_all()
                if not app.debug and not app.testing:
                    app.logger.info('All tables ensured via create_all')
            except Exception as e:
                if not app.debug and not app.testing:
                    app.logger.error(f'create_all failed: {e}')
    except Exception as e:
        if not app.debug and not app.testing:
            app.logger.error(f'Database connection failed: {e}')
        raise
    
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    
    from .views import bp
    app.register_blueprint(bp)
    
    # Обработчик ошибки 404 на уровне приложения
    @app.errorhandler(404)
    def not_found(error):
        """Обработчик ошибки 404 Not Found"""
        app.logger.warning(f"404 ошибка: {request.url}")
        return render_template("404.html"), 404
    
    # Настройка заголовков кеширования для статических файлов
    @app.after_request
    def add_cache_headers(response):
        if response.mimetype in ['image/png', 'image/x-icon', 'image/jpeg', 'image/gif', 'image/webp']:
            # Для иконок и изображений - короткий кеш
            response.cache_control.max_age = 300  # 5 минут
            response.cache_control.public = True
        elif response.mimetype in ['text/css', 'application/javascript']:
            # Для CSS и JS - средний кеш
            response.cache_control.max_age = 3600  # 1 час
            response.cache_control.public = True
        else:
            # Для остальных файлов - стандартный кеш
            response.cache_control.max_age = 86400  # 24 часа
            response.cache_control.public = True
        return response
    
    return app 