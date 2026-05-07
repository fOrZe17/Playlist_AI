# Playlist AI

Веб-приложение для генерации музыкальных плейлистов по текстовому запросу. Пользователь описывает настроение, жанр, ситуацию или исполнителя, а приложение получает рекомендации от Gemini, дополняет треки данными Deezer и сохраняет плейлисты в личном профиле.

## Возможности

- регистрация и авторизация пользователей;
- генерация плейлистов по промпту через Gemini;
- обогащение треков данными Deezer: исполнитель, обложка, длительность и ссылка;
- сохранение истории плейлистов в профиле;
- поиск и сортировка сохраненных плейлистов;
- избранные плейлисты с визуальной анимацией;
- коллаж обложек треков на карточке плейлиста;
- редактирование плейлиста: название, список треков, удаление плейлиста;
- экспорт плейлиста в CSV;
- редактирование профиля: никнейм, имя, фамилия, аватар, приватность и смена пароля.

## Стек

- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** Jinja2, HTML, CSS, чистый JavaScript
- **База данных:** PostgreSQL, SQLAlchemy Async, Alembic
- **Авторизация:** JWT, passlib/bcrypt
- **Внешние API:** Google Gemini, Deezer public API

## Переменные окружения

Создайте `.env` на основе `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/playlist_ai
SECRET_KEY=replace-with-secure-secret
AI_API_KEY=your-gemini-api-key
```

`DATABASE_URL` должен использовать драйвер `postgresql+asyncpg`.

## Локальный запуск

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

Примените миграции:

```bash
alembic upgrade head
```

Запустите приложение:

```bash
uvicorn app.main:app --reload
```

После запуска сайт будет доступен по адресу:

```text
http://127.0.0.1:8000
```

## Структура проекта

```text
app/
├── application/              # интерфейсы и use cases
├── domain/                   # доменные сущности и контракты репозиториев
├── infrastructure/           # БД, репозитории, Gemini и Deezer gateways
├── presentation/             # роутеры, схемы, шаблоны и static-файлы
├── config.py                 # настройки приложения
└── main.py                   # точка входа FastAPI

alembic/
└── versions/                 # миграции базы данных
```
