# EduFlow - Образовательная платформа

## ⚡ Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/switchxc/EduFlow.git
cd EduFlow
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
cp .env.example .env
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
YOOKASSA_SECRET_KEY=your-secret-key
YOOKASSA_TEST_MODE=True

# Цены подписок (в рублях)
SUBSCRIPTION_PRICE_1=99.00
SUBSCRIPTION_PRICE_3=249.00
SUBSCRIPTION_PRICE_6=449.00
SUBSCRIPTION_PRICE_12=749.00
```

### 4. Инициализация базы данных
```bash
python3 scripts/create_admin.py
```

Это создаст:
- Все таблицы базы данных
- Администратора с логином `admin` и паролем `admin123`
- Email администратора: `admin@ck7project.online`

### 5. Запуск приложения
```bash
python3 run.py
```

Приложение будет доступно по адресу: http://localhost:5000

## 👤 Администратор по умолчанию

- **Логин**: admin
- **Пароль**: admin123
- **Email**: admin@ck7project.online

⚠️ **Важно**: Измените пароль администратора после первого входа!

## 🛠 Скрипты администратора

### Создание администратора и инициализация БД
```bash
python3 scripts/create_admin.py
```

### Выдача подписки пользователю
```bash
python3 scripts/grant_subscription.py username
```

### Проверка подписки пользователя
```bash
python3 scripts/check_subscription.py username
```

### Очистка тикетов
```bash
python3 scripts/clear_tickets.py
```

## 📁 Структура проекта

```
EduFlow/
├── 📄 README.md                    # Документация проекта
├── 📄 requirements.txt             # Зависимости Python
├── 📄 run.py                      # Точка входа приложения
├── 📄 .env                        # Конфиденциальные настройки (не в git)
├── 📄 .env.example               # Пример настроек
├── 📄 app.db                     # База данных SQLite
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
│   ├── 📄 test_payment.py        # Тестирование платежей
│   └── 📄 test_site.py          # Тестирование сайта
│
└── 📁 .git/                      # Git репозиторий (скрыто)
```

### 📋 Описание основных компонентов:

**🔧 Основные файлы:**
- `run.py` - точка входа приложения
- `requirements.txt` - зависимости Python
- `app.db` - база данных SQLite
- `.env` - конфиденциальные настройки (не в git)

**🏗 Структура приложения:**
- `app/__init__.py` - инициализация Flask, конфигурация из переменных окружения
- `app/models.py` - модели User, Subject, Material, Payment, Ticket, etc.
- `app/views.py` - все маршруты и контроллеры
- `app/forms.py` - формы для регистрации, входа, создания материалов

**🎨 Frontend:**
- `app/templates/` - все HTML шаблоны с Jinja2
- `app/static/css/style.css` - основные стили
- `app/static/icons/` - иконки и favicon

**🛠 Утилиты:**
- `app/utils/email_service.py` - отправка email уведомлений
- `app/utils/payment_service.py` - интеграция с YooKassa
- `app/utils/file_storage.py` - управление загруженными файлами

**⚙️ Административные скрипты:**
- `scripts/create_admin.py` - создание БД и администратора
- `scripts/grant_subscription.py` - выдача подписок
- `scripts/check_subscription.py` - проверка подписок

## 🔧 Разработка

### Добавление новых функций
1. Создайте модель в `app/models.py`
2. Добавьте маршруты в `app/views.py`
3. Создайте шаблоны в `app/templates/`
4. Обновите базу данных: `python3 scripts/create_admin.py`

### Логи
Логи приложения сохраняются в `err.log`

### Отладка
Включите режим отладки в `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=True
```

**Автор**: switchxc  
**Версия**: 1.4.2 
**Последнее обновление**: 07.08.2025
