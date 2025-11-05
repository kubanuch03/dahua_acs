import ctypes
import logging
import time

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fMessCallBackEx1, fDisConnect
from NetSDK.SDK_Enum import CtrlType, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import (
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_CTRL_ACCESS_OPEN
)

class DeviceManager:
    """
    Класс для управления подключениями к устройствам Dahua и взаимодействия с SDK.
    Работает в рамках одного процесса-воркера.
    """
    def __init__(self, event_cfg: dict, ctrl_cfg: dict, on_event_callback, on_disconnect_callback):
        """
        Инициализирует менеджер устройств.

        :param event_cfg: Конфигурация для устройства-источника событий (терминала).
        :param ctrl_cfg: Конфигурация для устройства-цели команд (контроллера).
        :param on_event_callback: Python-функция, которая будет вызвана при получении события.
        :param on_disconnect_callback: Python-функция, которая будет вызвана при разрыве соединения.
        """
        self.event_config = event_cfg
        self.controller_config = ctrl_cfg
        self.on_event_callback = on_event_callback
        self.on_disconnect_callback = on_disconnect_callback

        self.netsdk = NetClient()
        self.event_login_id = 0
        self.controller_login_id = 0

        self.c_on_event = fMessCallBackEx1(self.on_event_callback)
        self.c_on_disconnect = fDisConnect(self.on_disconnect_callback)

    def initialize_sdk(self) -> bool:
        """
        Выполняет однократную инициализацию SDK и установку глобальных коллбэков.
        Должна быть вызвана один раз при старте воркера.
        """
        if not self.netsdk.InitEx(self.c_on_disconnect):
            logging.error("Критическая ошибка: не удалось инициализировать Dahua SDK!")
            return False
        
        self.netsdk.SetDVRMessCallBackEx1(self.c_on_event, 0)
        logging.info("Dahua SDK успешно инициализирован.")
        return True

    def _login(self, config: dict) -> int:
        """
        Внутренний метод для выполнения логина на устройство.
        
        :param config: Словарь с настройками подключения ('ip', 'port', 'user', 'password').
        :return: Login ID в случае успеха, иначе 0.
        """
        login_in = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        login_in.dwSize = ctypes.sizeof(login_in)
        login_in.szIP = config['ip'].encode()
        login_in.nPort = config['port']
        login_in.szUserName = config['user'].encode()
        login_in.szPassword = config['password'].encode()
        login_in.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        
        login_out = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        login_out.dwSize = ctypes.sizeof(login_out)

        login_id, _, err_msg = self.netsdk.LoginWithHighLevelSecurity(login_in, login_out)
        
        if login_id == 0:
            logging.error(f"Не удалось подключиться к {config['ip']}: {err_msg}")
            return 0
        
        return login_id

    def maintain_connections(self):
        """
        Проверяет и восстанавливает соединения с устройствами.
        Эту функцию нужно вызывать в основном цикле воркера.
        """
        if self.event_login_id == 0:
            new_login_id = self._login(self.event_config)
            if new_login_id != 0:
                self.event_login_id = new_login_id
                logging.info(f"Успешно подключен к источнику событий: {self.event_config['ip']}")
                if not self.netsdk.StartListenEx(self.event_login_id):
                    logging.error("Не удалось подписаться на события с терминала.")
                else:
                    logging.info("Подписка на события с терминала активна.")

        if self.controller_login_id == 0:
            new_login_id = self._login(self.controller_config)
            if new_login_id != 0:
                self.controller_login_id = new_login_id
                logging.info(f"Успешно подключен к контроллеру: {self.controller_config['ip']}")

    def open_door_command(self, channel_id: int) -> bool:
        if self.controller_login_id == 0:
            logging.error("Невозможно открыть дверь: контроллер не подключен.")
            return False

        in_params = NET_CTRL_ACCESS_OPEN()
        in_params.dwSize = ctypes.sizeof(in_params)
        in_params.nChannelID = channel_id
        
        out_params = ctypes.c_void_p(None)

        logging.debug(f"Отправка команды ControlDeviceEx(ACCESS_OPEN) на lLoginID: {self.controller_login_id}")
        
        success = self.netsdk.ControlDeviceEx(
            self.controller_login_id, 
            CtrlType.ACCESS_OPEN, 
            in_params,        
            out_params        
        )
        
        if not success:
            logging.error(f"Не удалось выполнить команду открытия двери {channel_id}.")
        
        return success

    def cleanup(self):
        """
        Корректно завершает все сессии и освобождает ресурсы SDK.
        """
        logging.info("Начало очистки ресурсов DeviceManager...")
        if self.event_login_id != 0:
            self.netsdk.StopListen(self.event_login_id)
            self.netsdk.Logout(self.event_login_id)
            logging.info(f"Сессия с источником событий ({self.event_config['ip']}) завершена.")
        
        if self.controller_login_id != 0:
            self.netsdk.Logout(self.controller_login_id)
            logging.info(f"Сессия с контроллером ({self.controller_config['ip']}) завершена.")
            
        self.netsdk.Cleanup()
        logging.info("Ресурсы Dahua SDK освобождены.")
        
        