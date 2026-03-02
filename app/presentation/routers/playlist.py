from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_playlist():
    """Генерация плейлиста с помощью ИИ. TODO: подключить use case GeneratePlaylist."""
    return {"message": "Генерация плейлиста — будет реализовано позже"}


@router.get("/list")
async def get_playlists():
    """Получение списка плейлистов. TODO: подключить use case GetUserPlaylists."""
    return {"message": "Список плейлистов — будет реализовано позже"}


@router.get("/{playlist_id}")
async def get_playlist(playlist_id: int):
    """Получение конкретного плейлиста. TODO: реализовать."""
    return {"message": f"Плейлист {playlist_id} — будет реализовано позже"}


@router.delete("/{playlist_id}")
async def delete_playlist(playlist_id: int):
    """Удаление плейлиста. TODO: реализовать."""
    return {"message": f"Удаление плейлиста {playlist_id} — будет реализовано позже"}
