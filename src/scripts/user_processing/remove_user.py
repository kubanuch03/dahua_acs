import ctypes
import time
from ctypes import (c_int, POINTER, Structure, c_ulong, c_char, c_ubyte,
                    c_void_p, c_bool, c_byte, cast, byref, create_string_buffer, sizeof) 
from datetime import datetime, timedelta

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Struct import (NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
                             NET_IN_ACCESS_USER_SERVICE_REMOVE, NET_OUT_ACCESS_USER_SERVICE_REMOVE)
from NetSDK.SDK_Enum import (EM_A_NET_EM_FAILCODE, EM_A_NET_EM_ACCESS_CTL_USER_SERVICE, 
                           EM_LOGIN_SPAC_CAP_TYPE)

DEVICE_IP = "192.168.10.157"
DEVICE_PORT = 37777
USERNAME = "admin"
PASSWORD = "S347367j"

USER_ID_TO_DELETE = "5001" 

def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

c_on_disconnect = fDisConnect(on_disconnect_callback)

def delete_user_from_device():
    print("1. Инициализация SDK...")
    netsdk = NetClient()
    is_sdk_initialized = netsdk.InitEx(c_on_disconnect)
    if not is_sdk_initialized:
        print("   Не удалось инициализировать SDK. Выход.")
        return

    login_id = 0
    try:
        print(f"2. Выполняется вход на устройство {DEVICE_IP}...")
        
        stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stuInParam.szIP = DEVICE_IP.encode()
        stuInParam.nPort = DEVICE_PORT
        stuInParam.szUserName = USERNAME.encode()
        stuInParam.szPassword = PASSWORD.encode()
        stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        
        stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        login_id, device_info, error_msg = netsdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
        
        if login_id == 0:
            print(f"   Ошибка входа! Сообщение: {error_msg}")
            return
        print(f"   Вход выполнен успешно. ID сессии: {login_id}")

        print(f"3. Подготовка данных для удаления пользователя '{USER_ID_TO_DELETE}'...")
        
        remove_params = NET_IN_ACCESS_USER_SERVICE_REMOVE()
        ctypes.memset(byref(remove_params), 0, sizeof(remove_params))
        remove_params.dwSize = sizeof(remove_params)
        remove_params.nUserNum = 1
        remove_params.szUserID = USER_ID_TO_DELETE.encode()

        fail_codes_array = (c_int * remove_params.nUserNum)()
        output_results = NET_OUT_ACCESS_USER_SERVICE_REMOVE()
        ctypes.memset(byref(output_results), 0, sizeof(output_results))
        output_results.dwSize = sizeof(output_results)
        output_results.nMaxRetNum = remove_params.nUserNum
        output_results.pFailCode = cast(fail_codes_array, POINTER(c_int))

        print(f"4. Отправка команды на удаление пользователя '{USER_ID_TO_DELETE}'...")
        
        success = netsdk.OperateAccessUserService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_USER_SERVICE.NET_EM_ACCESS_CTL_USER_SERVICE_REMOVE,
            remove_params,
            output_results,
            15000 
        )

        if success:
            print("   Вызов API OperateAccessUserService прошел успешно.")
            result_code_val = fail_codes_array[0]
            if result_code_val == 0: 
                print(f"   УСПЕШНО! Пользователь '{USER_ID_TO_DELETE}' был удален.")
            else:
                try:
                    error_name = EM_A_NET_EM_FAILCODE(result_code_val).name
                    print(f"   ОШИБКА ОПЕРАЦИИ: Не удалось удалить пользователя. Код: {error_name} ({result_code_val})")
                except ValueError:
                    print(f"   ОШИБКА ОПЕРАЦИИ: Не удалось удалить пользователя. Неизвестный код возврата: {result_code_val}")
        else:
            error_code = netsdk.GetLastError()
            print(f"   ОШИБКА SDK: Не удалось выполнить вызов API! Код ошибки SDK: {error_code}")

    except Exception as e:
        print(f"   Произошло непредвиденное исключение: {e}")
    finally:
        print("5. Завершение работы...")
        if login_id != 0:
            netsdk.Logout(login_id)
            print(f"   Выход из сессии {login_id} выполнен.")
        netsdk.Cleanup()
        print("   Очистка ресурсов SDK выполнена.")
        print("Скрипт завершен.")


if __name__ == "__main__":
    delete_user_from_device()