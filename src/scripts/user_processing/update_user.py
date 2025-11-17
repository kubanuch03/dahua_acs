import ctypes
import time
from ctypes import (c_int, POINTER, Structure, c_ulong, c_char, c_ubyte,
                    c_void_p, c_bool, c_byte, cast, byref, create_string_buffer, sizeof) 
from datetime import datetime, timedelta

# Основные импорты из SDK
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Struct import (NET_TIME, NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
                             NET_ACCESS_USER_INFO, NET_IN_ACCESS_USER_SERVICE_INSERT, 
                             NET_OUT_ACCESS_USER_SERVICE_INSERT)
from NetSDK.SDK_Enum import (EM_A_NET_EM_FAILCODE, EM_A_NET_EM_ACCESS_CTL_USER_SERVICE, 
                           EM_LOGIN_SPAC_CAP_TYPE, EM_A_NET_ENUM_USER_TYPE)

DEVICE_IP = "192.168.10.157"
DEVICE_PORT = 37777
USERNAME = "admin"
PASSWORD = "S347367j"

USER_ID_TO_UPDATE = "5001"  
NEW_USER_NAME = "Aidin Updated"  
NEW_PASSWORD = ""  

def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

c_on_disconnect = fDisConnect(on_disconnect_callback)

def update_user_on_device():
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

        print(f"3. Подготовка данных для обновления пользователя '{USER_ID_TO_UPDATE}'...")
        
        UserInfoArray = NET_ACCESS_USER_INFO * 1
        user_info_array = UserInfoArray()
        ctypes.memset(byref(user_info_array), 0, sizeof(user_info_array))
        
        user_info = user_info_array[0]
        user_info.szUserID = USER_ID_TO_UPDATE.encode()
        user_info.szName = NEW_USER_NAME.encode()
        if NEW_PASSWORD:
            user_info.szPsw = NEW_PASSWORD.encode()
            
        user_info.emUserType = EM_A_NET_ENUM_USER_TYPE.NET_ENUM_USER_TYPE_NORMAL
        user_info.nUserStatus = 0  

        now = datetime.now()
        future = now + timedelta(days=365 * 20)
        user_info.stuValidBeginTime = NET_TIME(now.year, now.month, now.day, 0, 0, 0)
        user_info.stuValidEndTime = NET_TIME(future.year, future.month, future.day, 23, 59, 59)

        insert_params = NET_IN_ACCESS_USER_SERVICE_INSERT()
        ctypes.memset(byref(insert_params), 0, sizeof(insert_params))
        insert_params.dwSize = sizeof(insert_params)
        insert_params.nInfoNum = 1
        insert_params.pUserInfo = cast(user_info_array, POINTER(NET_ACCESS_USER_INFO))

        fail_codes_array = (c_int * insert_params.nInfoNum)()
        output_results = NET_OUT_ACCESS_USER_SERVICE_INSERT()
        ctypes.memset(byref(output_results), 0, sizeof(output_results))
        output_results.dwSize = sizeof(output_results)
        output_results.nMaxRetNum = insert_params.nInfoNum
        output_results.pFailCode = cast(fail_codes_array, POINTER(c_int))

        print(f"4. Отправка команды на обновление пользователя '{USER_ID_TO_UPDATE}'...")
        
        success = netsdk.OperateAccessUserService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_USER_SERVICE.NET_EM_ACCESS_CTL_USER_SERVICE_INSERT,
            insert_params,
            output_results,
            15000 
        )

        if success:
            print("   Вызов API OperateAccessUserService прошел успешно.")
            result_code_val = fail_codes_array[0]
            if result_code_val == 0: 
                print(f"   УСПЕШНО! Данные пользователя '{USER_ID_TO_UPDATE}' были обновлены.")
            else:
                try:
                    error_name = EM_A_NET_EM_FAILCODE(result_code_val).name
                    print(f"   ОШИБКА ОПЕРАЦИИ: Не удалось обновить пользователя. Код: {error_name} ({result_code_val})")
                except ValueError:
                    print(f"   ОШИБКА ОПЕРАЦИИ: Не удалось обновить пользователя. Неизвестный код возврата: {result_code_val}")
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
    update_user_on_device()