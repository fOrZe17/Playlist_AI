from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/presentation/templates")


@router.get("/")
async def index(request: Request):
    """Главная страница."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login")
async def login_page(request: Request):
    """Страница входа."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
async def register_page(request: Request):
    """Страница регистрации."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/generate")
async def generate_page(request: Request):
    """Страница генерации плейлиста."""
    return templates.TemplateResponse("generate.html", {"request": request})


@router.get("/profile")
async def profile_page(request: Request):
    """Профиль с историей плейлистов."""
    return templates.TemplateResponse("profile.html", {"request": request})
