# coding=utf-8
import os
import sys
import ctypes
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, QDateTime
# Импорты ctypes из вашего предыдущего скрипта
from ctypes import (c_int, POINTER, Structure, c_ulong, c_char, c_ubyte,
                    c_void_p, c_bool, c_byte, cast, byref, create_string_buffer, sizeof)

# Основные импорты UI и SDK
from DeviceControlUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import (EM_DEV_CFG_TYPE, EM_LOGIN_SPAC_CAP_TYPE, 
                           EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE, EM_A_NET_EM_FAILCODE) # Добавлены ENUM для лиц
from NetSDK.SDK_Struct import (LOG_SET_PRINT_INFO, NET_TIME, C_LDWORD, C_LLONG, 
                             NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, 
                             CB_FUNCTYPE, NET_ACCESS_FACE_INFO, NET_IN_ACCESS_FACE_SERVICE_INSERT, 
                             NET_OUT_ACCESS_FACE_SERVICE_INSERT) # Добавлены структуры для лиц

# --- КОНСТАНТЫ ДЛЯ ДОБАВЛЕНИЯ ЛИЦА ---
NEW_USER_ID = "5001"
FACE_IMAGE_PATH = "./img/aidin_profile.jpg" # Убедитесь, что путь правильный

class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)
        
        # 界面初始化
        self._init_ui()

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

    # 初始化界面
    def _init_ui(self):
        self.Login_pushButton.setText('登录(Login)')
        # IP адрес из вашего русского скрипта
        self.IP_lineEdit.setText('192.168.10.157') 
        self.Port_lineEdit.setText('37777')
        self.Name_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('S347367j')

        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.OpenLog_pushButton.clicked.connect(self.openlog_btn_onclick)
        self.CloseLog_pushButton.clicked.connect(self.closelog_btn_onclick)
        self.GetTime_pushButton.clicked.connect(self.gettime_btn_onclick)
        self.SetTime_pushButton.clicked.connect(self.settime_btn_onclick)
        self.Restart_pushButton.clicked.connect(self.restart_btn_onclick)
        
        # --- НОВАЯ СВЯЗЬ ДЛЯ КНОПКИ ДОБАВЛЕНИЯ ЛИЦА ---
        # Предполагается, что в DeviceControlUI.py вы добавили кнопку с именем AddFace_pushButton
        if hasattr(self, 'AddFace_pushButton'):
            self.AddFace_pushButton.clicked.connect(self.add_face_btn_onclick)
        else:
            print("ПРЕДУПРЕЖДЕНИЕ: Кнопка 'AddFace_pushButton' не найдена в UI. Функция добавления лица не будет доступна.")

    def login_btn_onclick(self):
        # В этой реализации loginID это C_LLONG(), поэтому проверяем его значение .value
        if self.loginID.value == 0:
            ip = self.IP_lineEdit.text()
            port = int(self.Port_lineEdit.text())
            username = self.Name_lineEdit.text()
            password = self.Pwd_lineEdit.text()
            
            stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
            stuInParam.szIP = ip.encode()
            stuInParam.nPort = port
            stuInParam.szUserName = username.encode()
            stuInParam.szPassword = password.encode()
            stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
            stuInParam.pCapParam = None

            stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

            # loginID теперь C_LLONG, нужно получать его значение через .value
            login_id_val, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
            self.loginID.value = login_id_val
            
            if self.loginID.value != 0:
                self.setWindowTitle('设备控制(DeviceControl)-在线(OnLine)')
                self.Login_pushButton.setText('登出(Logout)')
            else:
                QMessageBox.about(self, '提示(prompt)', error_msg)
        else:
            result = self.sdk.Logout(self.loginID)
            if result:
                self.setWindowTitle("设备控制(DeviceControl)-离线(OffLine)")
                self.Login_pushButton.setText("登录(Login)")
                self.loginID.value = 0

    # --- НОВЫЙ МЕТОД ДЛЯ ДОБАВЛЕНИЯ ЛИЦА ---
    def add_face_btn_onclick(self):
        if self.loginID.value == 0:
            QMessageBox.warning(self, 'Ошибка', 'Необходимо сначала войти на устройство!')
            return

        try:
            # 1. Загрузка изображения
            with open(FACE_IMAGE_PATH, 'rb') as f:
                face_data_bytes = f.read()
            face_data_len = len(face_data_bytes)
            
            # 2. Выделение памяти и подготовка структур
            face_data_buffer = create_string_buffer(face_data_bytes, face_data_len)
            
            FaceInfoArray = NET_ACCESS_FACE_INFO * 1
            face_info_array = FaceInfoArray()
            ctypes.memset(byref(face_info_array), 0, sizeof(face_info_array))
            
            face_info = face_info_array[0]
            face_info.dwSize = sizeof(face_info)
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

            insert_params = NET_IN_ACCESS_FACE_SERVICE_INSERT()
            ctypes.memset(byref(insert_params), 0, sizeof(insert_params))
            insert_params.dwSize = sizeof(insert_params)
            insert_params.nFaceInfoNum = 1
            insert_params.pFaceInfo = cast(face_info_array, POINTER(NET_ACCESS_FACE_INFO))

            fail_codes_array = (c_int * insert_params.nFaceInfoNum)()
            output_results = NET_OUT_ACCESS_FACE_SERVICE_INSERT()
            ctypes.memset(byref(output_results), 0, sizeof(output_results))
            output_results.dwSize = sizeof(output_results)
            output_results.nMaxRetNum = insert_params.nFaceInfoNum
            output_results.pFailCode = cast(fail_codes_array, POINTER(c_int))
            
            # 3. Вызов API
            # Эта обертка, как мы выяснили, не требует byref()
            success = self.sdk.OperateAccessFaceService(
                self.loginID,
                EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE.NET_EM_ACCESS_CTL_FACE_SERVICE_INSERT,
                insert_params,
                output_results,
                20000
            )
            
            # 4. Обработка результата
            if success:
                result_code_val = fail_codes_array[0]
                if result_code_val == 0:
                    QMessageBox.information(self, 'Успех', f"Фотография лица успешно добавлена для пользователя '{NEW_USER_ID}'.")
                else:
                    try:
                        error_name = EM_A_NET_EM_FAILCODE(result_code_val).name
                        message = f"Ошибка при добавлении лица: {error_name} ({result_code_val})"
                    except ValueError:
                        message = f"Ошибка при добавлении лица: Неизвестный код возврата ({result_code_val})"
                    QMessageBox.critical(self, 'Ошибка операции', message)
            else:
                error_code = self.sdk.GetLastError()
                QMessageBox.critical(self, 'Ошибка SDK', f"Не удалось выполнить операцию! Код ошибки SDK: {error_code}")

        except FileNotFoundError:
             QMessageBox.critical(self, 'Ошибка файла', f"Файл изображения не найден по пути: {FACE_IMAGE_PATH}")
        except Exception as e:
            QMessageBox.critical(self, 'Непредвиденная ошибка', f"Произошло исключение: {e}")

    def openlog_btn_onclick(self):
        log_info = LOG_SET_PRINT_INFO()
        log_info.dwSize = sizeof(LOG_SET_PRINT_INFO)
        log_info.bSetFilePath = 1
        log_info.szLogFilePath = os.path.join(os.getcwd(), 'sdk_log.log').encode('gbk')
        result = self.sdk.LogOpen(log_info)
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def closelog_btn_onclick(self):
        result = self.sdk.LogClose()
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())

    def gettime_btn_onclick(self):
        if self.loginID.value == 0:
            QMessageBox.warning(self, '提示(prompt)', 'Пожалуйста, сначала войдите в систему (Please login first)')
            return
        
        time_struct = NET_TIME()
        result = self.sdk.GetDevConfig(self.loginID, int(EM_DEV_CFG_TYPE.TIMECFG), -1, byref(time_struct), sizeof(NET_TIME))
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            get_time = QDateTime(time_struct.dwYear, time_struct.dwMonth, time_struct.dwDay, time_struct.dwHour, time_struct.dwMinute, time_struct.dwSecond)
            self.Time_dateTimeEdit.setDateTime(get_time)

    def settime_btn_onclick(self):
        if self.loginID.value == 0:
            QMessageBox.warning(self, '提示(prompt)', 'Пожалуйста, сначала войдите в систему (Please login first)')
            return

        device_date = self.Time_dateTimeEdit.date()
        device_time = self.Time_dateTimeEdit.time()
        
        deviceDateTime = NET_TIME()
        deviceDateTime.dwYear = device_date.year()
        deviceDateTime.dwMonth = device_date.month()
        deviceDateTime.dwDay = device_date.day()
        deviceDateTime.dwHour = device_time.hour()
        deviceDateTime.dwMinute = device_time.minute()
        deviceDateTime.dwSecond = device_time.second()

        result = self.sdk.SetDevConfig(self.loginID, int(EM_DEV_CFG_TYPE.TIMECFG), -1, byref(deviceDateTime), sizeof(NET_TIME))
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
             QMessageBox.information(self, '提示(prompt)', 'Время успешно установлено (Time set successfully)')


    def restart_btn_onclick(self):
        if self.loginID.value == 0:
            QMessageBox.warning(self, '提示(prompt)', 'Пожалуйста, сначала войдите в систему (Please login first)')
            return
            
        result = self.sdk.RebootDev(self.loginID)
        if not result:
            QMessageBox.about(self, '提示(prompt)', self.sdk.GetLastErrorMessage())
        else:
            QMessageBox.about(self, '提示(prompt)', 'Перезагрузка начата (Restart initiated)')

    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("设备控制(DeviceControl)-离线(OffLine)")
        self.Login_pushButton.setText("登录(Login)")
        self.loginID.value = 0

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('设备控制(DeviceControl)-在线(OnLine)')
        self.Login_pushButton.setText('登出(Logout)')
        self.loginID.value = lLoginID # Восстанавливаем ID сессии

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        if self.loginID.value != 0:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = MyMainWindow()
    my_wnd.show()
    sys.exit(app.exec_())