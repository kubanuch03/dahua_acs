from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView, QApplication, QGroupBox, QMenu,QTableWidgetItem
from PyQt5.QtCore import Qt,QThread,pyqtSignal
from ctypes import *
import sys
import datetime
import types
import time
import os

from AlarmListenUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE

global hwnd

class VideoMotionCallBackAlarmInfo:
    def __init__(self):
        self.time_str = ""
        self.channel_str = ""
        self.alarm_type = ""
        self.status_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.channel_str = str(alarm_info.nChannelID)
        self.alarm_type = 'Событие Обнаружения Движения (VideoMotion event)' # Переведено с '动检事件（VideoMotion event)'
        if (alarm_info.nEventAction == 0):
            self.status_str = 'Импульс(Pulse)' 
        elif (alarm_info.nEventAction == 1):
            self.status_str = 'Начало(Start)' # Переведено с '开始(Start)'
        elif (alarm_info.nEventAction == 2):
            self.status_str = 'Конец(Stop)' # Переведено с '结束(Stop)'

class BackUpdateUIThread(QThread):
    # Через объект-член класса определяем сигнал
    update_date = pyqtSignal(int, object)

    # Обработка бизнес-логики
    def run(self):
        pass

@CB_FUNCTYPE(None, c_long, C_LLONG, POINTER(c_char), C_DWORD, POINTER(c_char), c_long, c_int, c_long, C_LDWORD)
def MessCallback(lCommand, lLoginID, pBuf, dwBufLen ,pchDVRIP, nDVRPort, bAlarmAckFlag, nEventID, dwUser):
    if(lLoginID != hwnd.loginID):
        return
    if(lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
        print('Enter MessCallback')
        alarm_info = cast(pBuf, POINTER(ALARM_MOTIONDETECT_INFO)).contents
        show_info = VideoMotionCallBackAlarmInfo()
        show_info.get_alarm_info(alarm_info)
        hwnd.backthread.update_date.emit(lCommand, show_info)

class StartListenWnd(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(StartListenWnd, self).__init__()
        self.setupUi(self)
        # Инициализация интерфейса
        self.init_ui()

        # Переменные и колбэки, используемые NetSDK
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        # Получение объекта NetSDK и инициализация
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # Установка функции обратного вызова для тревог
        self.sdk.SetDVRMessCallBackEx1(MessCallback,0)

        # Создание потока
        self.backthread = BackUpdateUIThread()
        # Подключение сигнала
        self.backthread.update_date.connect(self.update_ui)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # Запуск потока
        self.thread.started.connect(self.backthread.run)
        self.thread.start()


    def init_ui(self):
        self.IP_lineEdit.setText('192.168.10.108')
        self.Port_lineEdit.setText('37777')
        self.Username_lineEdit.setText('admin')
        self.Password_lineEdit.setText('S347367j')
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)

        self.Alarmlisten_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Stopalarmlisten_pushButton.clicked.connect(self.detach_btn_onclick)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.row = 0
        self.column = 0

    def log_open(self):
        log_info = LOG_SET_PRINT_INFO()
        log_info.dwSize = sizeof(LOG_SET_PRINT_INFO)
        log_info.bSetFilePath = 1
        log_info.szLogFilePath = os.path.join(os.getcwd(), 'sdk_log.log').encode('gbk')
        result = self.sdk.LogOpen(log_info)

    def login_btn_onclick(self):
        # Переведено: Установка заголовков таблицы: 'Номер по порядку', 'Время', 'Канал', 'Тип Тревоги', 'Статус'
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['№', 'Время', 'Канал', 'Тип Тревоги', 'Статус']) 
        ip = self.IP_lineEdit.text()
        port = int(self.Port_lineEdit.text())
        username = self.Username_lineEdit.text()
        password = self.Password_lineEdit.text()
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

        self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
        if self.loginID != 0:
            # Переведено: Заголовок окна: 'Подписка на Тревоги-Онлайн'
            self.setWindowTitle('Подписка на Тревоги-Онлайн') 
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            if (int(device_info.nChanNum) > 0):
                self.Alarmlisten_pushButton.setEnabled(True)
        else:
            # Переведено: Сообщение: 'Подсказка', 'Ошибка входа'
            QMessageBox.about(self, 'Подсказка', 'Ошибка входа: ' + error_msg) 

    def logout_btn_onclick(self):
        # Выход
        if (self.loginID == 0):
            return
        # Остановка подписки на тревоги
        self.sdk.StopListen(self.loginID)
        # Выход
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        # Переведено: Заголовок окна: 'Подписка на Тревоги-Офлайн'
        self.setWindowTitle("Подписка на Тревоги-Офлайн") 
        self.loginID = 0
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        # Переведено: Установка заголовков таблицы: 'Номер по порядку', 'Время', 'Канал', 'Тип Тревоги', 'Статус'
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['№', 'Время', 'Канал', 'Тип Тревоги', 'Статус']) 

    def attach_btn_onclick(self):
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        # Переведено: Установка заголовков таблицы: 'Номер по порядку', 'Время', 'Канал', 'Тип Тревоги', 'Статус'
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['№', 'Время', 'Канал', 'Тип Тревоги', 'Статус']) 
        result = self.sdk.StartListenEx(self.loginID)
        if result:
            # Переведено: Сообщение: 'Подсказка', 'Подписка на тревоги успешна'
            QMessageBox.about(self, 'Подсказка', "Подписка на тревоги успешна") 
            self.Stopalarmlisten_pushButton.setEnabled(True)
            self.Alarmlisten_pushButton.setEnabled(False)
        else:
            # Переведено: Сообщение: 'Подсказка', 'Ошибка'
            QMessageBox.about(self, 'Подсказка', 'Ошибка:' + str(self.sdk.GetLastError())) 

    def detach_btn_onclick(self):
        if (self.loginID > 0):
            self.sdk.StopListen(self.loginID)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(True)

    # Очистка ресурсов при закрытии главного окна
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.StopListen(self.loginID)
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Alarmlisten_tableWidget.clear()


    def update_ui(self, lCommand, show_info):
        print(f'Получена тревога! Команда: {lCommand}')
        if (lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
            if (self.row > 499):
                self.Alarmlisten_tableWidget.clear()
                self.Alarmlisten_tableWidget.setRowCount(0)
                # Переведено: Установка заголовков таблицы: 'Номер по порядку', 'Время', 'Канал', 'Тип Тревоги', 'Статус'
                self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(
                    ['№', 'Время', 'Канал', 'Тип Тревоги', 'Статус']) 
                self.row = 0
                self.Alarmlisten_tableWidget.viewport().update()
            self.Alarmlisten_tableWidget.setRowCount(self.row + 1)
            item = QTableWidgetItem(str(self.row + 1))
            self.Alarmlisten_tableWidget.setItem(self.row, self.column, item)
            item1 = QTableWidgetItem(show_info.time_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 1, item1)
            item2 = QTableWidgetItem(show_info.channel_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 2, item2)
            item3 = QTableWidgetItem(show_info.alarm_type)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 3, item3)
            item4 = QTableWidgetItem(show_info.status_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 4, item4)
            self.row += 1
                # обновление интерфейса
            self.Alarmlisten_tableWidget.update()
            self.Alarmlisten_tableWidget.viewport().update()


    # Реализация функции обратного вызова при разрыве соединения
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        # Переведено: Заголовок окна: 'Подписка на Тревоги-Офлайн'
        self.setWindowTitle("Подписка на Тревоги-Офлайн") 

    # Реализация функции обратного вызова при восстановлении соединения
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        # Переведено: Заголовок окна: 'Подписка на Тревоги-Онлайн'
        self.setWindowTitle('Подписка на Тревоги-Онлайн') 


if __name__ == '__main__':
    print(1111111111)
    app = QApplication(sys.argv)
    wnd = StartListenWnd()
    hwnd = wnd
    wnd.log_open()
    wnd.show()
    sys.exit(app.exec_())