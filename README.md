# cysu - Образовательная платформа

## ⚡ Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/cy7su/cysu.git
cd cysu
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
cp env.example .env
```

Отредактируйте `.env` файл, заполнив все необходимые переменные:

```env
# Секретный ключ (сгенерируйте уникальный)
SECRET_KEY=your-super-secret-key-here

# База данных
DATABASE_URL=sqlite:////path/to/your/project/app.db

# Email настройки
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# YooKassa настройки
YOOKASSA_SHOP_ID=your-shop-id
YOOKASHA_SECRET_KEY=your-secret-key
YOOKASSA_TEST_MODE=True

# Цены подписок (в рублях)
SUBSCRIPTION_PRICE_1=89.00
SUBSCRIPTION_PRICE_3=199.00
SUBSCRIPTION_PRICE_6=349.00
SUBSCRIPTION_PRICE_12=469.00

# Настройки загрузки файлов
UPLOAD_FOLDER=app/static/uploads
CHAT_FILES_FOLDER=app/static/chat_files
TICKET_FILES_FOLDER=app/static/ticket_files
MAX_CONTENT_LENGTH=20971520

# Логирование
LOG_FILE=logs/app.log
LOG_LEVEL=INFO
```

### 4. Инициализация базы данных
```bash
python3 scripts/create_admin.py
```

Это создаст:
- Все таблицы базы данных
- Администратора с логином `admin` и паролем `admin123`
- Email администратора: `admin@cysu.ru`

### 5. Запуск приложения
```bash
python3 run.py
```

Приложение будет доступно по адресу: http://localhost:8001

## 👤 Администратор по умолчанию

- **Логин**: admin
- **Пароль**: admin123
- **Email**: admin@cysu.ru

⚠️ **Важно**: Измените пароль администратора после первого входа!

## 🛠 Скрипты администратора

### Основные скрипты

#### Создание администратора и инициализация БД
```bash
python3 scripts/create_admin.py
```

#### Выдача подписки пользователю
```bash
python3 scripts/grant_subscription.py username
```

#### Проверка подписки пользователя
```bash
python3 scripts/check_subscription.py username
```

#### Очистка тикетов
```bash
python3 scripts/clear_tickets.py
```

#### Очистка коротких ссылок
```bash
python3 scripts/clear_shortlinks.py
```

#### Добавление колонки group_id
```bash
python3 scripts/add_group_id_column.py
```

#### Создание таблиц групп
```bash
python3 scripts/create_groups_tables.py
```

### Тестовые скрипты

#### Тестирование безопасности
```bash
python3 scripts/test_security.py
```
Проверяет основные аспекты безопасности приложения.

#### Расширенное тестирование безопасности
```bash
python3 scripts/advanced_security_test.py
```
Комплексная проверка безопасности с детальным отчетом.

#### Тестирование базы данных
```bash
python3 scripts/test_database.py
```
Проверяет целостность и производительность базы данных.

#### Тестирование email
```bash
python3 scripts/test_email.py
```
Тестирует отправку email уведомлений.

#### Тестирование платежей
```bash
python3 scripts/test_payment.py
```
Проверяет интеграцию с YooKassa.

#### Тестирование сайта
```bash
python3 scripts/test_site.py
```
Комплексное тестирование функциональности сайта.

#### Тестирование утилит
```bash
python3 scripts/test_utils.py
```
Тестирует основные утилиты приложения.

#### Очистка всех тестов
```bash
python3 scripts/cleanup_all_tests.py
```
Очищает все тестовые данные.

## 📁 Структура проекта

```
cysu/
├── 📄 README.md                    # Документация проекта
├── 📄 requirements.txt             # Зависимости Python
├── 📄 run.py                      # Точка входа приложения (порт 8001)
├── 📄 .env                        # Конфиденциальные настройки (не в git)
├── 📄 env.example                # Пример настроек
├── 📄 app.db                     # База данных SQLite
├── 📄 logs/                      # Директория для логов
│   └── 📄 app.log               # Основной лог приложения
│
├── 📁 app/                       # Основное приложение Flask
│   ├── 📄 __init__.py            # Инициализация Flask и конфигурация
│   ├── 📄 models.py              # Модели базы данных (User, Subject, Material, etc.)
│   ├── 📄 views.py               # Маршруты и контроллеры
│   ├── 📄 forms.py               # Формы WTForms для регистрации, входа, etc.
│   │
│   ├── 📁 static/                # Статические файлы
│   │   ├── 📁 css/
│   │   │   └── 📄 style.css      # Основные стили
│   │   ├── 📁 icons/             # Иконки и favicon
│   │   ├── 📁 uploads/           # Загруженные файлы пользователей
│   │   ├── 📁 chat_files/        # Файлы чата
│   │   └── 📁 ticket_files/      # Файлы тикетов
│   │
│   ├── 📁 templates/             # HTML шаблоны
│   │   ├── 📄 base.html          # Базовый шаблон
│   │   ├── 📄 index.html         # Главная страница
│   │   ├── 📄 profile.html       # Профиль пользователя
│   │   ├── 📄 account.html       # Настройки аккаунта
│   │   ├── 📄 404.html           # Страница 404 ошибки
│   │   │
│   │   ├── 📁 auth/              # Страницы авторизации
│   │   │   ├── 📄 login.html
│   │   │   ├── 📄 register.html
│   │   │   ├── 📄 email_verification.html
│   │   │   ├── 📄 password_reset_request.html
│   │   │   └── 📄 password_reset_confirm.html
│   │   │
│   │   ├── 📁 admin/             # Административная панель
│   │   │   ├── 📄 users.html
│   │   │   ├── 📄 subjects.html
│   │   │   └── 📄 materials.html
│   │   │
│   │   ├── 📁 subjects/          # Страницы предметов
│   │   │   ├── 📄 subject_detail.html
│   │   │   └── 📄 material_detail.html
│   │   │
│   │   ├── 📁 tickets/           # Система тикетов
│   │   │   ├── 📄 tickets.html
│   │   │   ├── 📄 ticket_detail.html
│   │   │   └── 📄 user_ticket_detail.html
│   │   │
│   │   ├── 📁 payment/           # Система платежей
│   │   │   ├── 📄 subscription.html
│   │   │   ├── 📄 payment_status.html
│   │   │   └── 📄 success.html
│   │   │
│   │   └── 📁 static/            # Статические страницы
│   │       ├── 📄 privacy.html
│   │       ├── 📄 terms.html
│   │       └── 📄 wiki.html
│   │
│   ├── 📁 services/              # Сервисы
│   │   └── 📄 shortlink_service.py # Сервис коротких ссылок
│   │
│   └── 📁 utils/                 # Утилиты и сервисы
│       ├── 📄 email_service.py   # Отправка email
│       ├── 📄 payment_service.py # Интеграция с YooKassa
│       └── 📄 file_storage.py    # Управление файлами
│
├── 📁 scripts/                   # Административные скрипты
│   ├── 📄 create_admin.py        # Создание администратора и инициализация БД
│   ├── 📄 grant_subscription.py  # Выдача подписки пользователю
│   ├── 📄 check_subscription.py  # Проверка подписки пользователя
│   ├── 📄 clear_tickets.py       # Очистка старых тикетов
│   ├── 📄 clear_shortlinks.py    # Очистка коротких ссылок
│   ├── 📄 add_group_id_column.py # Добавление колонки group_id
│   ├── 📄 create_groups_tables.py # Создание таблиц групп
│   ├── 📄 test_security.py       # Тестирование безопасности
│   ├── 📄 advanced_security_test.py # Расширенное тестирование безопасности
│   ├── 📄 test_database.py       # Тестирование базы данных
│   ├── 📄 test_email.py          # Тестирование email
│   ├── 📄 test_payment.py        # Тестирование платежей
│   ├── 📄 test_site.py           # Тестирование сайта
│   ├── 📄 test_utils.py          # Тестирование утилит
│   └── 📄 cleanup_all_tests.py   # Очистка всех тестов
│
└── 📁 .git/                      # Git репозиторий (скрыто)
```

### 📋 Описание основных компонентов:

**🔧 Основные файлы:**
- `run.py` - точка входа приложения (порт 8001)
- `requirements.txt` - зависимости Python
- `app.db` - база данных SQLite
- `.env` - конфиденциальные настройки (не в git)
- `logs/app.log` - логи приложения

**🏗 Структура приложения:**
- `app/__init__.py` - инициализация Flask, конфигурация из переменных окружения
- `app/models.py` - модели User, Subject, Material, Payment, Ticket, etc.
- `app/views.py` - все маршруты и контроллеры
- `app/forms.py` - формы для регистрации, входа, создания материалов

**🎨 Frontend:**
- `app/templates/` - все HTML шаблоны с Jinja2
- `app/templates/404.html` - кастомная страница 404 ошибки
- `app/static/css/style.css` - основные стили
- `app/static/icons/` - иконки и favicon

**🛠 Утилиты и сервисы:**
- `app/utils/email_service.py` - отправка email уведомлений
- `app/utils/payment_service.py` - интеграция с YooKassa
- `app/utils/file_storage.py` - управление загруженными файлами
- `app/services/shortlink_service.py` - сервис коротких ссылок

**⚙️ Административные скрипты:**
- `scripts/create_admin.py` - создание БД и администратора
- `scripts/grant_subscription.py` - выдача подписок
- `scripts/check_subscription.py` - проверка подписок
- `scripts/clear_tickets.py` - очистка тикетов
- `scripts/clear_shortlinks.py` - очистка коротких ссылок
- `scripts/add_group_id_column.py` - добавление колонки group_id
- `scripts/create_groups_tables.py` - создание таблиц групп
- `scripts/test_security.py` - тестирование безопасности
- `scripts/advanced_security_test.py` - расширенное тестирование безопасности
- `scripts/test_database.py` - тестирование базы данных
- `scripts/test_email.py` - тестирование email
- `scripts/test_payment.py` - тестирование платежей
- `scripts/test_site.py` - тестирование сайта
- `scripts/test_utils.py` - тестирование утилит
- `scripts/cleanup_all_tests.py` - очистка всех тестов

## 🔧 Разработка

### Добавление новых функций
1. Создайте модель в `app/models.py`
2. Добавьте маршруты в `app/views.py`
3. Создайте шаблоны в `app/templates/`
4. Обновите базу данных: `python3 scripts/create_admin.py`

### Логи
Логи приложения сохраняются в `logs/app.log`

### Отладка
Включите режим отладки в `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=True
```

## 🆕 Новые возможности

### Сервис коротких ссылок
- Автоматическое создание коротких ссылок для материалов
- Управление и очистка коротких ссылок
- Интеграция с системой материалов

### Система групп
- Поддержка группировки пользователей
- Таблицы для управления группами
- Скрипты для создания структуры групп

### Расширенное тестирование
- Комплексные скрипты для тестирования всех аспектов приложения
- Автоматизированные проверки безопасности
- Тестирование производительности базы данных
- Тестирование утилит и сервисов

### Улучшенная безопасность
- Расширенные проверки безопасности
- Тестирование уязвимостей
- Мониторинг безопасности

### Обновленные цены подписок
- 1 месяц: 89₽
- 3 месяца: 199₽
- 6 месяцев: 349₽
- 12 месяцев: 469₽

**Автор**: cy7su  
**Версия**: 1.6.4
**Последнее обновление**: 27.08.2025
