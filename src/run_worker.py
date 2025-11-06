# run_worker.py

import logging
import time
import redis
import json
import ctypes
import base64
import sys

from utils.config import config
from utils.logger import *
from core.device_manager import DeviceManager
from NetSDK.SDK_Enum import SDK_ALARM_TYPE, NET_ACCESS_DOOROPEN_METHOD
from NetSDK.SDK_Struct import NET_A_ALARM_ACCESS_CTL_EVENT_INFO

class Worker:
    def __init__(self):
        # Настройка
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db'],
            password=config['redis']['password'],
            decode_responses=True # Сразу получать строки
        )
        
        self.manager = DeviceManager(
            event_cfg=config['event_source_device'],
            ctrl_cfg=config['command_target_controller'],
            on_event_callback=self.on_event_callback,
            on_disconnect_callback=self.on_disconnect_callback
        )

    def on_disconnect_callback(self, lLoginID, pchDVRIP, *args):
        try:
            ip = pchDVRIP.decode()
            logging.warning(f"Устройство {ip} отключилось.")
            # Сбросим login_id, чтобы maintain_connections его переподключил
            if self.manager.event_login_id == lLoginID:
                self.manager.event_login_id = 0
            if self.manager.controller_login_id == lLoginID:
                self.manager.controller_login_id = 0
        except Exception:
            logging.warning("Неизвестное устройство отключилось.")

    def on_event_callback(self, lCommand, lLoginID, pBuf, dwBufLen, *args):
        """
        ПРИНИМАЕТ событие от SDK и кладет в Redis.
        Эта функция выполняется в потоке SDK и должна быть очень быстрой.
        """
        if lCommand == SDK_ALARM_TYPE.ALARM_ACCESS_CTL_EVENT:
            try:
                event_data_bytes = ctypes.string_at(pBuf, dwBufLen)
                base64_string = base64.b64encode(event_data_bytes).decode('utf-8')

                message = {
                    "type": "access_control_event",
                    "data_b64": base64_string,
                    "data_len": dwBufLen # Сохраним и длину буфера
                }

                # Публикуем в канал для обработки
                self.redis_client.publish("dahua_events_raw", json.dumps(message))
                logging.debug("Событие контроля доступа отправлено в очередь на обработку.")
            except Exception as e:
                logging.error(f"Ошибка в on_event_callback: {e}", exc_info=True)
        return 0

    def process_sdk_event(self, message):
        """
        ОБРАБАТЫВАЕТ событие из Redis. Здесь основная логика.
        """
        try:
            event = json.loads(message['data'])
            if event.get("type") == "access_control_event":
                base64_string = event['data_b64']
                data_len = event['data_len']
                
                original_bytes = base64.b64decode(base64_string.encode('utf-8'))
                
                event_info = ctypes.cast(original_bytes, ctypes.POINTER(NET_A_ALARM_ACCESS_CTL_EVENT_INFO)).contents

                logging.info(f"="*80)
                
                logging.info(f"""
                             Получено событие от UserID: {event_info.szUserID.decode(errors='ignore')}, 
                             Метод: {NET_ACCESS_DOOROPEN_METHOD(event_info.emOpenMethod).name}, 
                             Статус: {'Успех' if event_info.bStatus else 'Неудача'}
                             
                             Дополнительно:
                             Номер карты: {event_info.szCardNo.decode(errors='ignore')}
                             Passw: {event_info.szPwd.decode(errors='ignore')}
                             szReaderID: {event_info.szReaderID.decode(errors='ignore')}
                             nAge: {event_info.nAge}
                             nLiftNo: {event_info.nLiftNo}
                             nNumbers: {event_info.nNumbers}
                             nDoor: {event_info.nDoor}
                             szDoorName: {event_info.szDoorName.decode(errors='ignore')}
                             szSnapURL: {event_info.szSnapURL.decode(errors='ignore')}
                             """
                             
                             
                             )
                logging.info(f"="*80)

                if (event_info.bStatus and 
                    event_info.emOpenMethod == NET_ACCESS_DOOROPEN_METHOD.FACE_RECOGNITION):
                    
                    door_to_open = event_info.nDoor
                    logging.info(f"Успешное распознавание лица на двери {door_to_open}. Отправка команды на открытие...")
                    
                    success = self.manager.open_door_command(door_to_open)
                    
                    if success:
                        logging.info(f"Команда на открытие двери {door_to_open} успешно отправлена на контроллер.")
                    else:
                        logging.warning(f"Не удалось отправить команду на открытие двери {door_to_open}.")
                

        except Exception as e:
            logging.error(f"Ошибка при обработке события из Redis: {e}", exc_info=True)

    def run(self):
        """Основной цикл воркера."""
        if not self.manager.initialize_sdk():
            return

        event_pubsub = self.redis_client.pubsub()
        event_pubsub.subscribe(**{"dahua_events_raw": self.process_sdk_event})
        event_thread = event_pubsub.run_in_thread(sleep_time=0.01, daemon=True)  

        logging.info("Воркер запущен. Ожидание событий...")

        try:
            while True:
                self.manager.maintain_connections()
                time.sleep(5)  

        except KeyboardInterrupt:
            logging.info("Остановка воркера...")
        finally:
            event_thread.stop()
            self.manager.cleanup()
            logging.info("Воркер остановлен.")

if __name__ == "__main__":
    worker = Worker()
    worker.run()