import logging
import sys



"""Настраивает систему логирования для вывода в консоль и в файл."""
logger = logging.getLogger()
logger.setLevel(logging.INFO)   

# Создаем форматтер для сообщений
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создаем обработчик для записи в файл
# Указываем кодировку utf-8 для корректной работы с кириллицей
file_handler = logging.FileHandler('dahua_events.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)