import ctypes
import logging
import queue  # Используем стандартный модуль queue
from NetSDK.SDK_Enum import NET_ACCESS_DOOROPEN_METHOD, SDK_ALARM_TYPE
from NetSDK.SDK_Struct import NET_A_ALARM_ACCESS_CTL_EVENT_INFO

class EventHandler:
    """
    Класс, работающий в отдельном потоке, который извлекает события из очереди
    и выполняет их обработку.
    """
    def __init__(self, event_queue: queue.Queue):
        """
        Инициализирует обработчик.
        :param event_queue: Общая очередь для получения событий от DeviceManager.
        """
        self.event_queue = event_queue
        self.is_running = False

    def run(self):
        """
        Основной цикл работы обработчика. Эту функцию нужно запускать в отдельном потоке.
        """
        self.is_running = True
        logging.info("Обработчик событий запущен и готов к работе.")
        while self.is_running:
            try:
                event_type, event_data_tuple = self.event_queue.get(timeout=1)
                
                event_data, data_len = event_data_tuple

                # В зависимости от типа события, вызываем соответствующий метод обработки
                if event_type == SDK_ALARM_TYPE.ALARM_ACCESS_CTL_EVENT:
                    self.process_access_control_event(event_data, data_len)
                
                # elif event_type == SDK_ALARM_TYPE.ALARM_VIDEO_LOSS:
                #     self.process_video_loss_event(event_data, data_len)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Критическая ошибка в цикле обработчика событий: {e}", exc_info=True)

    def process_access_control_event(self, data: bytes, data_len: int):
        """
        Обрабатывает событие контроля доступа.
        :param data: Сырые бинарные данные события.
        :param data_len: Длина этих данных.
        """
        logging.info("\n" + "="*30)
        logging.info("Обработка события контроля доступа...")
        
        try:
            p_event_info = ctypes.cast(data, ctypes.POINTER(NET_A_ALARM_ACCESS_CTL_EVENT_INFO))
            event_info = p_event_info.contents
            
            utc_time = event_info.RealUTC
            time_str = (f"{utc_time.dwYear}-{utc_time.dwMonth:02d}-{utc_time.dwDay:02d} "
                        f"{utc_time.dwHour:02d}:{utc_time.dwMinute:02d}:{utc_time.dwSecond:02d}")
            logging.info(f"Время события: {time_str}")
            
            logging.info(f"Номер двери: {event_info.nDoor}")
            logging.info(f"Статус прохода: {'Успешно' if event_info.bStatus else 'Неуспешно'}")
            
            method_name = NET_ACCESS_DOOROPEN_METHOD(event_info.emOpenMethod).name
            logging.info(f"Метод открытия: {method_name} ({event_info.emOpenMethod})")
            
            logging.info(f"Номер карты: {event_info.szCardNo.decode(errors='ignore')}")
            logging.info(f"UserID: {event_info.szUserID.decode(errors='ignore')}")
            
            if not event_info.bStatus:
                logging.warning(f"Код ошибки: {hex(event_info.nErrorCode)}")

            struct_size = ctypes.sizeof(NET_A_ALARM_ACCESS_CTL_EVENT_INFO)
            
            if data_len > struct_size:
                logging.info("Обнаружено прикрепленное изображение в событии.")
                offset = struct_size
                length = data_len - offset

                image_data = data[offset : offset + length]

                filename = f"event_{time_str.replace(':', '-').replace(' ', '_')}.jpg"
                try:
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    logging.info(f"Изображение сохранено в файл: {filename}")
                except IOError as e:
                    logging.error(f"Не удалось сохранить файл изображения {filename}: {e}")
            else:
                logging.info("Изображение в данном событии отсутствует.")

            # db_connector.save_event(
            #     timestamp=time_str,
            #     user_id=event_info.szUserID.decode(errors='ignore'),
            #     status=event_info.bStatus,
            #     method=method_name,
            #     image_path=filename if data_len > struct_size else None
            # )
            ###################################

        except Exception as e:
            logging.error(f"Ошибка при разборе данных события контроля доступа: {e}", exc_info=True)
            
        logging.info("Обработка события завершена." + "\n" + "="*30)

    def stop(self):
        """
        Сигнализирует основному циклу о необходимости завершения.
        """
        self.is_running = False
        logging.info("Обработчик событий останавливается...")