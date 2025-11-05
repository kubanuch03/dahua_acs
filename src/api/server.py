# src/api/server.py
from fastapi import FastAPI

app = FastAPI(title="Access Control API")

# Эта функция позволит главному файлу "внедрить" сервисы в приложение
def set_services(door_svc=None, user_svc=None):
    app.state.door_service = door_svc
    app.state.user_service = user_svc