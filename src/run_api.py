# run_api.py
import uvicorn
from api.server import app
from api.routes import router
from services.door_service import DoorService
from utils.config import config
from utils.logger import *


# Создаем сервисы, которые будут работать с Redis
door_service = DoorService()
# user_service = UserService() # и т.д.


app.state.door_service = door_service
app.include_router(router, prefix="/api")

# Запускаем сервер
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config['api_server']['host'],
        port=config['api_server']['port']
    )