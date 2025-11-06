# -*- coding: utf-8 -*-
import ctypes
import time
from ctypes import c_int # byref убран отсюда

# --- Ваши импорты (предполагается, что они настроены правильно) ---
from NetSDK.SDK_Struct import NET_DEVICEINFO_Ex, NET_CTRL_ACCESS_OPEN
from NetSDK.NetSDK import NetClient  
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Enum import CtrlType  

DEVICE_IP = "192.168.10.156"
DEVICE_PORT = 37777
USERNAME = "admin"
PASSWORD = "S347367j"
DOOR_CHANNEL_ID = 0

def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

# Оборачиваем Python-функцию в тип коллбэка, понятный для C
c_on_disconnect = fDisConnect(on_disconnect_callback)


def open_the_door():
    """
    Основная функция для подключения и открытия двери с использованием класса NetClient.
    """
    print("1. Инициализация SDK...")
    netsdk = NetClient()
    
    is_sdk_initialized = netsdk.InitEx(c_on_disconnect)
    if not is_sdk_initialized:
        print("Не удалось инициализировать SDK. Выход.")
        return

    login_id = 0

    try:
        print(f"2. Выполняется вход на устройство {DEVICE_IP}...")
        
        login_id, device_info, error_message = netsdk.LoginEx2(
            DEVICE_IP,
            DEVICE_PORT,
            USERNAME,
            PASSWORD
        )

        if login_id == 0:
            print(f"Ошибка входа! Сообщение: {error_message}")
            return

        print(f"   Вход выполнен успешно. ID сессии: {login_id}")
        print(f"   Тип устройства: {device_info.nDVRType}, Каналов: {device_info.nChanNum}")

        print(f"3. Отправка команды на открытие двери №{DOOR_CHANNEL_ID}...")

        open_params = NET_CTRL_ACCESS_OPEN()
        open_params.dwSize = ctypes.sizeof(NET_CTRL_ACCESS_OPEN)
        open_params.nChannelID = DOOR_CHANNEL_ID
        open_params.szUserID = b"PythonScript"
        
        # ***** ИСПРАВЛЕННЫЙ ВЫЗОВ *****
        success = netsdk.ControlDevice(
            login_id,
            CtrlType.ACCESS_OPEN,
            open_params  
        )
        
        if success:
            print("   Команда на открытие двери успешно отправлена!")
        else:
            print("   Не удалось отправить команду! Смотрите лог ошибок выше.")

        time.sleep(2)

    except Exception as e:
        print(f"Произошло непредвиденное исключение: {e}")
    finally:
        print("4. Завершение работы...")
        if login_id != 0:
            print(f"   Выход из сессии {login_id}...")
            netsdk.Logout(login_id)
        
        print("   Очистка ресурсов SDK...")
        netsdk.Cleanup()
        print("Скрипт завершен.")


if __name__ == "__main__":
    open_the_door()