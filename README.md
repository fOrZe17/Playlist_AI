# Playlist AI — ВИ МПИИ

Веб-интерфейс для создания музыкальных плейлистов с применением технологии искусственного интеллекта.

## Стек технологий

- **Backend:** Python, FastAPI, Uvicorn
- **Шаблонизация:** Jinja2
- **База данных:** PostgreSQL, SQLAlchemy (async), Alembic
- **Аутентификация:** JWT (python-jose), passlib

## Установка и запуск

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env, указав свои значения

# Запуск сервера
uvicorn app.main:app --reload
```

## Структура проекта

```
app/
├── main.py          # Точка входа FastAPI
├── config.py        # Настройки приложения
├── database.py      # Подключение к БД
├── models/          # SQLAlchemy модели
├── routers/         # Маршруты API и страниц
├── services/        # Бизнес-логика (AI, музыка)
├── schemas/         # Pydantic-схемы
├── templates/       # Jinja2 HTML-шаблоны
└── static/          # CSS, JS
```
