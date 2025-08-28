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
    app = Flask(__name__, instance_path=None, instance_relative_config=False)
    
    # Конфигурация из переменных окружения
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    # Конфигурация базы данных - создаем в корне проекта
    db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Создаем директорию для базы данных если её нет
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    

    
    # Конфигурация загрузки файлов
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    app.config['CHAT_FILES_FOLDER'] = os.getenv('CHAT_FILES_FOLDER', 'app/static/chat_files')
    app.config['TICKET_FILES_FOLDER'] = os.getenv('TICKET_FILES_FOLDER', 'app/static/ticket_files')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 20 * 1024 * 1024))
    
    # Создаем необходимые директории для загрузки файлов
    for folder in [app.config['UPLOAD_FOLDER'], app.config['CHAT_FILES_FOLDER'], app.config['TICKET_FILES_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
    
    # Конфигурация почты
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
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
    app.config['LOG_FILE'] = os.getenv('LOG_FILE', 'logs/app.log')
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    
    # Настройка логирования
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
    
    # Настройка кэширования: только SVG кэшируется
    @app.after_request
    def add_cache_headers(response):
        if request.endpoint == 'static':
            filename = request.path.split('/')[-1]
            if filename.endswith('.svg'):
                # SVG файлы кэшируются на 1 год
                response.cache_control.max_age = 31536000
                response.cache_control.public = True
            else:
                # Все остальное не кэшируется
                response.cache_control.no_cache = True
                response.cache_control.no_store = True
                response.cache_control.must_revalidate = True
        return response
    
    db.init_app(app)
    
    # Проверка подключения к базе данных и создание таблиц
    try:
        with app.app_context():
            # Проверяем подключение
            db.engine.connect()
            app.logger.info('Database connection successful')
            
            # Принудительно создаем все таблицы
            try:
                db.create_all()
                app.logger.info('All tables created successfully')
            except Exception as e:
                app.logger.error(f'Error creating tables: {e}')
                # Если не удалось создать таблицы, логируем ошибку но не прерываем работу
                app.logger.error(f'create_all failed: {e}')
    except Exception as e:
        app.logger.error(f'Database connection failed: {e}')
        if not app.debug and not app.testing:
            raise
    
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    
    from .views import bp
    app.register_blueprint(bp)
    
    # Context processor для проверки технических работ
    @app.context_processor
    def inject_maintenance_mode():
        """Добавляет информацию о режиме технических работ в шаблоны"""
        try:
            from .models import SiteSettings
            maintenance_mode = SiteSettings.get_setting('maintenance_mode', False)
            return dict(maintenance_mode=maintenance_mode)
        except Exception as e:
            app.logger.error(f'Error in inject_maintenance_mode: {e}')
            return dict(maintenance_mode=False)
    
    # Middleware для проверки технических работ
    @app.before_request
    def check_maintenance_mode():
        """Проверяет режим технических работ"""
        # Пропускаем статические файлы и некоторые маршруты
        if request.endpoint == 'static' or request.endpoint in ['main.maintenance', 'main.login', 'main.logout']:
            return
        
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from .models import SiteSettings
            from flask_login import current_user
            
            # Проверяем, включен ли режим технических работ
            maintenance_mode = SiteSettings.get_setting('maintenance_mode', False)
            if maintenance_mode:
                # Если пользователь не админ, перенаправляем на страницу технических работ
                if not current_user.is_authenticated or not current_user.is_admin:
                    # Перенаправляем на страницу технических работ
                    return redirect(url_for('main.maintenance'))
        except Exception as e:
            app.logger.error(f'Error checking maintenance mode: {e}')
    
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