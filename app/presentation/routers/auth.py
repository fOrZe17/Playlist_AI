from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """Регистрация нового пользователя. TODO: подключить use case RegisterUser."""
    return {"message": "Регистрация — будет реализовано позже"}


@router.post("/login")
async def login():
    """Авторизация пользователя. TODO: подключить use case LoginUser."""
    return {"message": "Авторизация — будет реализовано позже"}


@router.post("/logout")
async def logout():
    """Выход из аккаунта. TODO: реализовать."""
    return {"message": "Выход — будет реализовано позже"}
