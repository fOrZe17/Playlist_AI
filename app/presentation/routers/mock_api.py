import hashlib
import random
import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter()

# In-memory хранилище (тестовый режим)
_users: dict[str, dict] = {}
_tokens: dict[str, str] = {}  # token -> email
_playlists: dict[str, list[dict]] = {}  # email -> [playlists]

MOCK_TRACKS = [
    {"title": "Blinding Lights", "artist": "The Weeknd", "duration": "3:20", "cover": "🌆"},
    {"title": "Bohemian Rhapsody", "artist": "Queen", "duration": "5:55", "cover": "👑"},
    {"title": "Shape of You", "artist": "Ed Sheeran", "duration": "3:53", "cover": "🎸"},
    {"title": "Starboy", "artist": "The Weeknd", "duration": "3:50", "cover": "⭐"},
    {"title": "Levitating", "artist": "Dua Lipa", "duration": "3:23", "cover": "🚀"},
    {"title": "Watermelon Sugar", "artist": "Harry Styles", "duration": "2:54", "cover": "🍉"},
    {"title": "Save Your Tears", "artist": "The Weeknd", "duration": "3:35", "cover": "💧"},
    {"title": "Peaches", "artist": "Justin Bieber", "duration": "3:18", "cover": "🍑"},
    {"title": "Good 4 U", "artist": "Olivia Rodrigo", "duration": "2:58", "cover": "🔥"},
    {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "duration": "2:21", "cover": "💜"},
    {"title": "Montero", "artist": "Lil Nas X", "duration": "2:17", "cover": "🦋"},
    {"title": "Kiss Me More", "artist": "Doja Cat ft. SZA", "duration": "3:28", "cover": "💋"},
    {"title": "drivers license", "artist": "Olivia Rodrigo", "duration": "4:02", "cover": "🚗"},
    {"title": "Positions", "artist": "Ariana Grande", "duration": "2:52", "cover": "✨"},
    {"title": "Dynamite", "artist": "BTS", "duration": "3:19", "cover": "💣"},
    {"title": "Circles", "artist": "Post Malone", "duration": "3:35", "cover": "🔵"},
    {"title": "Sunflower", "artist": "Post Malone & Swae Lee", "duration": "2:38", "cover": "🌻"},
    {"title": "Shallow", "artist": "Lady Gaga & Bradley Cooper", "duration": "3:35", "cover": "🌊"},
]


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_email_from_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return _tokens.get(token)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GenerateRequest(BaseModel):
    prompt: str
    title: str = ""


@router.post("/register")
async def register(data: RegisterRequest):
    if data.email in _users:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    token = secrets.token_hex(32)
    _users[data.email] = {
        "email": data.email,
        "password_hash": _hash_password(data.password),
        "created_at": datetime.now().isoformat(),
    }
    _tokens[token] = data.email
    _playlists.setdefault(data.email, [])

    return {"token": token, "email": data.email}


@router.post("/login")
async def login(data: LoginRequest):
    user = _users.get(data.email)
    if not user or user["password_hash"] != _hash_password(data.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = secrets.token_hex(32)
    _tokens[token] = data.email
    return {"token": token, "email": data.email}


@router.post("/generate")
async def generate(data: GenerateRequest, authorization: str | None = Header(default=None)):
    email = _get_email_from_token(authorization)
    if not email:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    count = random.randint(5, 8)
    tracks = random.sample(MOCK_TRACKS, k=min(count, len(MOCK_TRACKS)))

    title = data.title or f"Плейлист: {data.prompt[:40]}"
    playlist = {
        "id": len(_playlists.get(email, [])) + 1,
        "title": title,
        "prompt": data.prompt,
        "tracks": tracks,
        "created_at": datetime.now().isoformat(),
    }

    _playlists.setdefault(email, []).append(playlist)
    return playlist


@router.get("/profile")
async def profile(authorization: str | None = Header(default=None)):
    email = _get_email_from_token(authorization)
    if not email:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    user = _users.get(email, {})
    return {
        "email": email,
        "created_at": user.get("created_at", ""),
        "playlists_count": len(_playlists.get(email, [])),
    }


@router.get("/playlists")
async def playlists(authorization: str | None = Header(default=None)):
    email = _get_email_from_token(authorization)
    if not email:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    return {"playlists": _playlists.get(email, [])}
