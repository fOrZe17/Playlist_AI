from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.presentation.routers import api, auth, pages

app = FastAPI(title="Playlist AI — ВИ МПИИ")

# Статические файлы
app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")

# Подключение роутеров
app.include_router(pages.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(api.router, prefix="/api", tags=["api"])
