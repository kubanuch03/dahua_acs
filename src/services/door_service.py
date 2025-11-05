# src/services/door_service.py
import logging
import redis
import json
from utils.config import config

class DoorService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db']
        )

    def open_door(self, channel_id: int) -> bool:
        """
        Отправляет команду на открытие двери в очередь Redis.
        """
        try:
            command = {
                "action": "open_door",
                "channel_id": channel_id
            }
            self.redis_client.publish("dahua_commands", json.dumps(command))
            logging.info(f"Команда на открытие двери {channel_id} отправлена в очередь Redis.")
            return True
        except Exception as e:
            logging.error(f"Не удалось отправить команду в Redis: {e}")
            return False