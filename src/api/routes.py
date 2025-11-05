# src/api/routes.py
import logging
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/door/{channel_id}/open", summary="Принудительно открыть дверь")
async def open_door_endpoint(channel_id: int, request: Request):
    logging.info(f"Получен API-запрос на открытие двери {channel_id}")
    
    door_service = request.app.state.door_service
    
    if not door_service:
        raise HTTPException(status_code=500, detail="Сервис управления дверью не инициализирован.")

    success = door_service.open_door(channel_id)
    
    if not success:
        raise HTTPException(status_code=503, detail="Не удалось выполнить команду. Проверьте подключение к контроллеру.")
        
    return {"status": "ok", "message": f"Команда на открытие двери {channel_id} отправлена"}