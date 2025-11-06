import ctypes
import time
from ctypes import (c_int, POINTER, Structure, c_ulong, c_char, c_ubyte,
                    c_void_p, c_bool, c_byte, cast, byref)
from datetime import datetime, timedelta

# Основные импорты из SDK
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Struct import NET_TIME, NET_ACCESS_FACE_INFO, NET_IN_ACCESS_FACE_SERVICE_UPDATE, NET_OUT_ACCESS_FACE_SERVICE_UPDATE
from NetSDK.SDK_Enum import EM_A_NET_EM_FAILCODE, EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE
 
   
# --- КОНСТАНТЫ ---
DEVICE_IP = "192.168.10.157"
DEVICE_PORT = 37777
USERNAME = "admin"
PASSWORD = "S347367j"
NEW_USER_ID = "5001"
FACE_IMAGE_PATH = "./img/aidin_profile.jpg"

 
def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

c_on_disconnect = fDisConnect(on_disconnect_callback)

 
def update_face_to_user():
    print("1. Инициализация SDK...")
    netsdk = NetClient()
    is_sdk_initialized = netsdk.InitEx(c_on_disconnect)
    if not is_sdk_initialized:
        print("Не удалось инициализировать SDK. Выход.")
        return

    login_id = 0
    try:
        print(f"2. Выполняется вход на устройство {DEVICE_IP}...")
        login_id, _, error_message = netsdk.LoginEx2(DEVICE_IP, DEVICE_PORT, USERNAME, PASSWORD)
        if login_id == 0:
            print(f"Ошибка входа! Сообщение: {error_message}")
            return
        print(f"   Вход выполнен успешно. ID сессии: {login_id}")

        print(f"3. Загрузка изображения лица из файла: {FACE_IMAGE_PATH}...")
        try:
            with open(FACE_IMAGE_PATH, 'rb') as f: face_data_bytes = f.read()
        except Exception as e:
            print(f"   Ошибка при чтении файла изображения: {e}")
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

        insert_params = NET_IN_ACCESS_FACE_SERVICE_UPDATE()
        insert_params.dwSize = ctypes.sizeof(insert_params)
        insert_params.nFaceInfoNum = 1
        insert_params.pFaceInfo = face_info_array

        fail_codes = (c_int * insert_params.nFaceInfoNum)()
        output_results = NET_OUT_ACCESS_FACE_SERVICE_UPDATE()
        output_results.dwSize = ctypes.sizeof(output_results)
        output_results.nMaxRetNum = insert_params.nFaceInfoNum
        output_results.pFailCode = cast(fail_codes, POINTER(c_int))

        print("4. Отправка данных лица на контроллер...")

        
        success = netsdk.OperateAccessFaceService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE.NET_EM_ACCESS_CTL_FACE_SERVICE_INSERT,
            insert_params,
            output_results,
            15000
        )

        if success:
          
            print(f"   УСПЕШНО! Фотография лица добавлена для пользователя '{NEW_USER_ID}'.")
             
                # try:
                #     error_name = EM_A_NET_EM_FAILCODE(result_code_val).name
                #     print(f"   Ошибка при добавлении: {error_name} ({result_code_val})")
                # except ValueError:
                #     print(f"   Ошибка при добавлении: Неизвестный код возврата ({result_code_val})")
        else:
            error_code = netsdk.GetLastError()
            print(f"   Не удалось выполнить операцию! Код ошибки SDK: {error_code}")

    except Exception as e:
        print(f"Произошло непредвиденное исключение: {e}")
    finally:
        print("5. Завершение работы...")
        if login_id != 0:
            netsdk.Logout(login_id)
            print(f"   Выход из сессии {login_id}...")
        netsdk.Cleanup()
        print("   Очистка ресурсов SDK...")
        print("Скрипт завершен.")


if __name__ == "__main__":
    update_face_to_user()