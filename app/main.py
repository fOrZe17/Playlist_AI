from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.presentation.routers import auth, playlist, pages, mock_api

app = FastAPI(title="Playlist AI — ВИ МПИИ")

# Статические файлы
app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")

# Jinja2 шаблоны
templates = Jinja2Templates(directory="app/presentation/templates")

# Подключение роутеров
app.include_router(pages.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(playlist.router, prefix="/playlist", tags=["playlist"])
app.include_router(mock_api.router, prefix="/api", tags=["mock-api"])
