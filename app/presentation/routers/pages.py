from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/presentation/templates")


@router.get("/")
async def index(request: Request):
    """Главная страница."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/login")
async def login_page(request: Request):
    """Страница входа."""
    return templates.TemplateResponse(request, "login.html")


@router.get("/register")
async def register_page(request: Request):
    """Страница регистрации."""
    return templates.TemplateResponse(request, "register.html")


@router.get("/generate")
async def generate_page(request: Request):
    """Страница генерации плейлиста."""
    return templates.TemplateResponse(request, "generate.html")


@router.get("/profile")
async def profile_page(request: Request):
    """Профиль с историей плейлистов."""
    return templates.TemplateResponse(request, "profile.html")


@router.get("/profile/edit")
async def profile_edit_page(request: Request):
    return templates.TemplateResponse(request, "profile_edit.html")
