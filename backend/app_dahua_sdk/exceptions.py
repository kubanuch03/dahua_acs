



class DahuaSDKError(Exception):
    """Базовый класс для всех ошибок SDK."""
    def __init__(self, message, sdk_error_code=None):
        super().__init__(message)
        self.sdk_error_code = sdk_error_code

class DeviceConnectionError(DahuaSDKError):
    """Ошибка подключения или входа на устройство."""
    pass

class UserAlreadyExistsError(DahuaSDKError):
    """Пользователь с таким ID уже существует."""
    pass

class UserNotFoundError(DahuaSDKError):
    """Пользователь не найден."""
    pass