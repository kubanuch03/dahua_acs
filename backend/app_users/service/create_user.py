# -*- coding: utf-8 -*-
import ctypes
import time
from ctypes import c_int, byref, POINTER, Structure, c_ulong

from NetSDK.NetSDK import NetClient  
from NetSDK.SDK_Callback import fDisConnect
from NetSDK.SDK_Struct import NET_ACCESS_USER_INFO, NET_TIME, NET_IN_ACCESS_USER_SERVICE_INSERT, NET_OUT_ACCESS_USER_SERVICE_INSERT
from NetSDK.SDK_Enum import EM_A_NET_EM_ACCESS_CTL_USER_SERVICE, EM_A_NET_ENUM_USER_TYPE, EM_A_NET_EM_FAILCODE

NEW_USER_ID="5001"
NEW_USER_NAME="Test User 5001"
NEW_CARD_NO="50015001"
NEW_USER_PASSWORD="123456"

# Права доступа
ACCESSIBLE_DOORS = [0] 
ACCESSIBLE_SCHEDULES = [1]

def on_disconnect_callback(login_id, ip_address, port, user_data):
    ip_str = ip_address.decode()
    print(f"!!! ВНИМАНИЕ: Устройство {ip_str} отключилось.")

c_on_disconnect = fDisConnect(on_disconnect_callback)


def create_user():
    print("1. Инициализация SDK...")
    netsdk = NetClient()
    
    is_sdk_initialized = netsdk.InitEx(c_on_disconnect)
    if not is_sdk_initialized:
        print("Не удалось инициализировать SDK. Выход.")
        return

    login_id = 0
    #TODO: импортируй с api/env_config.py
    try:
        print(f"2. Выполняется вход на устройство {DEVICE_IP}...")
        
        login_id, device_info, error_message = netsdk.LoginEx2(DEVICE_IP, DEVICE_PORT, USERNAME, PASSWORD)

        if login_id == 0:
            print(f"Ошибка входа! Сообщение: {error_message}")
            return

        print(f"   Вход выполнен успешно. ID сессии: {login_id}")

        print(f"3. Создание пользователя с ID: {NEW_USER_ID}...")

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
        full_door_array = (c_int * 32)(-1)  
        for i, door_id in enumerate(ACCESSIBLE_DOORS):
            full_door_array[i] = door_id
        user_info.nDoors = full_door_array

        user_info.nTimeSectionNum = len(ACCESSIBLE_SCHEDULES)
        full_schedule_array = (c_int * 32)(-1)  
        for i, schedule_id in enumerate(ACCESSIBLE_SCHEDULES):
            full_schedule_array[i] = schedule_id
        user_info.nTimeSectionNo = full_schedule_array
        # --------------------------------------------------------------------

        user_info.stuValidBeginTime = NET_TIME(2020, 1, 1, 0, 0, 0)
        user_info.stuValidEndTime = NET_TIME(2037, 12, 31, 23, 59, 59)

        insert_params = NET_IN_ACCESS_USER_SERVICE_INSERT()
        insert_params.dwSize = ctypes.sizeof(insert_params)
        insert_params.nInfoNum = 1
        insert_params.pUserInfo = ctypes.pointer(user_info)

        FailCodeArray = c_int * insert_params.nInfoNum
        fail_codes = FailCodeArray()
        
        output_results = NET_OUT_ACCESS_USER_SERVICE_INSERT()
        output_results.dwSize = ctypes.sizeof(output_results)
        output_results.nMaxRetNum = insert_params.nInfoNum
        output_results.pFailCode = ctypes.cast(fail_codes, POINTER(c_int))

        print("4. Отправка данных на контроллер...")
        success = netsdk.OperateAccessUserService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_USER_SERVICE.NET_EM_ACCESS_CTL_USER_SERVICE_INSERT,
            insert_params,     
            output_results,
            5000
        )
        
        if success:
            result_code_val = fail_codes[0]
            result_enum = EM_A_NET_EM_FAILCODE(result_code_val)
            
            if result_enum == EM_A_NET_EM_FAILCODE.NET_EM_FAILCODE_NOERROR:
                print(f"   Успешно! Пользователь '{NEW_USER_NAME}' с ID '{NEW_USER_ID}' создан.")
            elif result_enum == EM_A_NET_EM_FAILCODE.NET_EM_FAILCODE_RECORD_ALREADY_EXISTS:
                print(f"   Ошибка: Пользователь с ID '{NEW_USER_ID}' уже существует.")
            else:
                print(f"   Ошибка при создании пользователя: {result_enum.name} ({result_code_val})")
        else:
            error_code = netsdk.GetLastError()
            if error_code == 7:
                 print(f"   Не удалось выполнить операцию! Код ошибки SDK: {error_code} (NET_PARAM_ERROR - Ошибка в параметрах)")
            else:
                 print(f"   Не удалось выполнить операцию! Код ошибки SDK: {error_code}")

        time.sleep(1)

    except Exception as e:
        print(f"Произошло непредвиденное исключение: {e}")
    finally:
        print("5. Завершение работы...")
        if login_id != 0:
            print(f"   Выход из сессии {login_id}...")
            netsdk.Logout(login_id)
        
        print("   Очистка ресурсов SDK...")
        netsdk.Cleanup()
        print("Скрипт завершен.")


if __name__ == "__main__":
    create_user()
