# cysu - Образовательная платформа

**learn & code** - ДЛЯ ВСЕХ ТЕХ КТО НЕНАВИДИТ MOODLE


<img width="1904" height="1080" alt="{0718D01C-29B2-4B5F-A42B-B1EDE550523A}" src="https://github.com/user-attachments/assets/6c772425-422a-4ef3-9529-62d181f960f8" style="border-radius: 12px;" />


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
- Email администратора: `admin@cysu.ru`

### 5. Запуск приложения
```bash
python3 run.py
```

Приложение будет доступно по адресу: http://localhost:5000

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

## 📁 Структура проекта

```
cysu/
├── 📄 README.md                    # Документация проекта
├── 📄 requirements.txt             # Зависимости Python
├── 📄 run.py                      # Точка входа приложения
├── 📄 .env                        # Конфиденциальные настройки (не в git)
├── 📄 .env.example               # Пример настроек
├── 📄 app.db                     # База данных SQLite
├── 📄 err.log                    # Логи ошибок
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
│   └── 📁 utils/                 # Утилиты и сервисы
│       ├── 📄 email_service.py   # Отправка email
│       ├── 📄 payment_service.py # Интеграция с YooKassa
│       └── 📄 file_storage.py    # Управление файлами
│
├── 📁 scripts/                   # Административные скрипты
├── 📄 create_admin.py        # Создание администратора и инициализация БД
├── 📄 grant_subscription.py  # Выдача подписки пользователю
├── 📄 check_subscription.py  # Проверка подписки пользователя
├── 📄 clear_tickets.py       # Очистка старых тикетов
├── 📄 test_security.py       # Тестирование безопасности
├── 📄 advanced_security_test.py # Расширенное тестирование безопасности
├── 📄 test_database.py       # Тестирование базы данных
├── 📄 test_email.py          # Тестирование email
├── 📄 test_payment.py        # Тестирование платежей
└── 📄 test_site.py           # Тестирование сайта

                    # Git репозиторий (скрыто)
```

### 📋 Описание основных компонентов:

**🔧 Основные файлы:**
- `run.py` - точка входа приложения
- `requirements.txt` - зависимости Python
- `app.db` - база данных SQLite
- `.env` - конфиденциальные настройки (не в git)
- `err.log` - логи ошибок приложения

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

**🛠 Утилиты:**
- `app/utils/email_service.py` - отправка email уведомлений
- `app/utils/payment_service.py` - интеграция с YooKassa
- `app/utils/file_storage.py` - управление загруженными файлами

**⚙️ Административные скрипты:**
- `scripts/create_admin.py` - создание БД и администратора
- `scripts/grant_subscription.py` - выдача подписок
- `scripts/check_subscription.py` - проверка подписок
- `scripts/clear_tickets.py` - очистка тикетов
- `scripts/test_security.py` - тестирование безопасности
- `scripts/advanced_security_test.py` - расширенное тестирование безопасности
- `scripts/test_database.py` - тестирование базы данных
- `scripts/test_email.py` - тестирование email
- `scripts/test_payment.py` - тестирование платежей
- `scripts/test_site.py` - тестирование сайта

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

## 🆕 Новые возможности

### Страница 404
- Кастомная страница 404 ошибки с современным дизайном
- Анимированные элементы и градиентные эффекты
- Кнопки в стиле главной страницы

### Расширенное тестирование
- Комплексные скрипты для тестирования всех аспектов приложения
- Автоматизированные проверки безопасности
- Тестирование производительности базы данных

### Улучшенная безопасность
- Расширенные проверки безопасности
- Тестирование уязвимостей
- Мониторинг безопасности

**Автор**: cy7su  
**Версия**: 1.5.1
**Последнее обновление**: 10.08.2025
