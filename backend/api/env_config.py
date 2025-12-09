import os

from dotenv import load_dotenv

load_dotenv(".env.backend", override=True)


def get_required_env_var(name: str, default: str | None = None) -> str:
    """
    Получает обязательную переменную окружения.
    Если переменная не найдена, вызывает ошибку ValueError.
    """
    value = os.getenv(name)
    if value is None:
        raise ValueError(
            f"Обязательная переменная окружения '{name}' отсутствует в .env файле."
        )
    return value


def get_int_env_var(name: str, default: int) -> int:
    """
    Получает числовую (integer) переменную окружения.
    Если переменная не найдена или не является числом, возвращает значение по умолчанию.
    """
    try:
        return int(os.getenv(name, str(default)))
    except (ValueError, TypeError):
        return default


def get_bool_env_var(name: str, default: bool = False) -> bool:
    """
    Получает логическую (boolean) переменную окружения.
    Значения "true", "1", "yes" (без учета регистра) считаются True.
    В остальных случаях возвращает False или значение по умолчанию.
    """
    value = os.getenv(name, str(default)).lower()
    return value in ("true", "1", "yes")



DEVICE_IP= get_required_env_var("DEVICE_IP","192.168.10.157")
DEVICE_PORT= get_int_env_var("DEVICE_PORT",37777)


USERNAME=get_required_env_var("USERNAME","admin")
PASSWORD=get_required_env_var("PASSWORD","S347367j")
