# -*- coding: utf-8 -*-
import resource

import ctypes
import time
from ctypes import c_int, POINTER, c_ubyte, c_void_p, cast, byref
from datetime import datetime, timedelta

# Импорты Dahua SDK
from NetSDK.NetSDK import NetClient  
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Struct import (
    NET_ACCESS_USER_INFO, NET_TIME,
    NET_IN_ACCESS_USER_SERVICE_INSERT, NET_OUT_ACCESS_USER_SERVICE_INSERT,
    NET_IN_ACCESS_FACE_SERVICE_UPDATE, NET_OUT_ACCESS_FACE_SERVICE_UPDATE,
    NET_IN_ACCESS_FACE_SERVICE_INSERT, NET_OUT_ACCESS_FACE_SERVICE_INSERT,
    NET_ACCESS_FACE_INFO
)
from NetSDK.SDK_Enum import (
    EM_A_NET_EM_ACCESS_CTL_USER_SERVICE,
    EM_A_NET_ENUM_USER_TYPE,
    EM_A_NET_EM_FAILCODE,
    EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE
)


# ============ НАСТРОЙКИ ============
DEVICE_IP = "192.168.10.157"
DEVICE_PORT = 37777
USERNAME = "admin"
PASSWORD = "S347367j"

NEW_USER_ID = "5001"
NEW_USER_NAME = "Test User 5001"
NEW_CARD_NO = "50015001"
NEW_USER_PASSWORD = "123456"
USER_PHOTO_PATH = "./img/tilek2.jpeg"

ACCESSIBLE_DOORS = [0]
ACCESSIBLE_SCHEDULES = [1]

# ===================================


def get_memory_usage():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


initial_memory = get_memory_usage()
print(f"Потребление памяти до запуска: {initial_memory / 1024:.2f} MB")



def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

c_on_disconnect = fDisConnect(on_disconnect_callback)


def create_user_with_photo():
    print("1. Инициализация SDK...")
    netsdk = NetClient()
    if not netsdk.InitEx(c_on_disconnect):
        print("Не удалось инициализировать SDK. Выход.")
        return

    login_id = 0
    try:
        print(f"2. Вход на устройство {DEVICE_IP}...")
        login_id, device_info, error_message = netsdk.LoginEx2(DEVICE_IP, DEVICE_PORT, USERNAME, PASSWORD)
        if login_id == 0:
            print(f"Ошибка входа: {error_message}")
            return
        print(f"   Вход выполнен успешно. ID сессии: {login_id}")

        print(f"3. Создание пользователя '{NEW_USER_NAME}' (ID: {NEW_USER_ID})...")

        user_info = NET_ACCESS_USER_INFO()
        ctypes.memset(ctypes.addressof(user_info), 0, ctypes.sizeof(user_info))
        user_info.dwSize = ctypes.sizeof(user_info)
        user_info.bIsValid = True
        user_info.szUserID = NEW_USER_ID.encode()
        user_info.szName = NEW_USER_NAME.encode()
        user_info.szCardNo = NEW_CARD_NO.encode()
        user_info.szPsw = NEW_USER_PASSWORD.encode()
        user_info.emUserType = EM_A_NET_ENUM_USER_TYPE.NET_ENUM_USER_TYPE_NORMAL
        user_info.nUserStatus = 0
        user_info.bFirstEnter = False
        user_info.nDoorNum = len(ACCESSIBLE_DOORS)

        # Двери
        full_door_array = (c_int * 32)(-1)
        for i, door_id in enumerate(ACCESSIBLE_DOORS):
            full_door_array[i] = door_id
        user_info.nDoors = full_door_array

        # Расписания
        user_info.nTimeSectionNum = len(ACCESSIBLE_SCHEDULES)
        full_schedule_array = (c_int * 32)(-1)
        for i, schedule_id in enumerate(ACCESSIBLE_SCHEDULES):
            full_schedule_array[i] = schedule_id
        user_info.nTimeSectionNo = full_schedule_array

        # Временной диапазон действия
        user_info.stuValidBeginTime = NET_TIME(2020, 1, 1, 0, 0, 0)
        user_info.stuValidEndTime = NET_TIME(2037, 12, 31, 23, 59, 59)

        # Вставка пользователя
        insert_in = NET_IN_ACCESS_USER_SERVICE_INSERT()
        insert_in.dwSize = ctypes.sizeof(insert_in)
        insert_in.nInfoNum = 1
        insert_in.pUserInfo = ctypes.pointer(user_info)

        fail_codes = (c_int * insert_in.nInfoNum)()
        insert_out = NET_OUT_ACCESS_USER_SERVICE_INSERT()
        insert_out.dwSize = ctypes.sizeof(insert_out)
        insert_out.nMaxRetNum = insert_in.nInfoNum
        insert_out.pFailCode = ctypes.cast(fail_codes, POINTER(c_int))

        success = netsdk.OperateAccessUserService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_USER_SERVICE.NET_EM_ACCESS_CTL_USER_SERVICE_INSERT,
            insert_in,
            insert_out,
            5000
        )

        if not success:
            print(f"❌ Ошибка создания пользователя. Код SDK: {netsdk.GetLastError()}")
            return

        if fail_codes[0] == EM_A_NET_EM_FAILCODE.NET_EM_FAILCODE_NOERROR:
            print("✅ Пользователь успешно создан.")
        else:
            print(f"⚠️ Ошибка при создании пользователя: {fail_codes[0]}")

        
        print("4. Добавление фотографии...")

        try:
            with open(USER_PHOTO_PATH, "rb") as f:
                face_data_bytes = f.read()
        except FileNotFoundError:
            print(f"Файл {USER_PHOTO_PATH} не найден!")
            return

        print(f"   Изображение загружено. Размер: {len(face_data_bytes)} байт.")

        face_data_len = len(face_data_bytes)
        face_data_buffer = (c_ubyte * face_data_len)(*face_data_bytes)

        FaceInfoArray = NET_ACCESS_FACE_INFO * 1
        face_info_array = FaceInfoArray()
        face_info = face_info_array[0]

        ctypes.memset(byref(face_info), 0, ctypes.sizeof(face_info))

        face_info.dwSize = ctypes.sizeof(face_info)
        face_info.szUserID = NEW_USER_ID.encode()
        face_info.bEnable = True
        face_info.nFacePhoto = 1
        face_info.nInFacePhotoLen[0] = face_data_len
        face_info.pFacePhoto[0] = cast(face_data_buffer, c_void_p)

        now = datetime.now()
        future = now + timedelta(days=365 * 20)
        face_info.stuValidStartTime = NET_TIME(now.year, now.month, now.day, now.hour, now.minute, now.second)
        face_info.stuValidEndTime = NET_TIME(future.year, future.month, future.day, future.hour, future.minute, future.second)
        face_info.stuUpdateTime = NET_TIME(now.year, now.month, now.day, now.hour, now.minute, now.second)

        face_in = NET_IN_ACCESS_FACE_SERVICE_INSERT()
        face_in.dwSize = ctypes.sizeof(NET_IN_ACCESS_FACE_SERVICE_UPDATE)
        face_in.nFaceInfoNum = 1
        face_in.pFaceInfo = face_info_array

        fail_codes = (c_int * face_in.nFaceInfoNum)()
        face_out = NET_OUT_ACCESS_FACE_SERVICE_INSERT()
        face_out.dwSize = ctypes.sizeof(NET_OUT_ACCESS_FACE_SERVICE_INSERT)
        face_out.nMaxRetNum = face_in.nFaceInfoNum
        face_out.pFailCode = cast(fail_codes, POINTER(c_int))

        success = netsdk.OperateAccessFaceService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE.NET_EM_ACCESS_CTL_FACE_SERVICE_INSERT,
            face_in,
            face_out,
            15000
        )

        if success:
            if fail_codes[0] == EM_A_NET_EM_FAILCODE.NET_EM_FAILCODE_NOERROR:
                print("✅ Фото успешно добавлено пользователю.")
            else:
                print(f"⚠️ Ошибка при добавлении фото: {fail_codes[0]}")
        else:
            err = netsdk.GetLastError()
            print(f"❌ Ошибка добавления фото. Код SDK: {err}")

    except Exception as e:
        print(f"Произошло исключение: {e}")

    finally:
        print("5. Завершение работы...")
        if login_id != 0:
            netsdk.Logout(login_id)
        netsdk.Cleanup()
        print("Скрипт завершен.")


if __name__ == "__main__":
    create_user_with_photo()
    final_memory = get_memory_usage()
    print(f"Потребление памяти после запуска: {final_memory / 1024:.2f} MB")
    print(f"Разница: {(final_memory - initial_memory) / 1024:.2f} MB")
