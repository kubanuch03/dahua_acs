#!/bin/bash

# 1. Находим точный путь, где pip установил библиотеки NetSDK
# Эта команда спросит у Python, где лежит пакет NetSDK
LIB_PATH=$(python3 -c "import NetSDK; import os; print(os.path.dirname(NetSDK.__file__))")

# 2. Проверяем, что путь найден
if [ -z "$LIB_PATH" ]; then
    echo "ОШИБКА: Не удалось найти установленный пакет NetSDK. Установите его через pip."
    exit 1
fi

# 3. Формируем полный путь к .so файлам и выводим его для проверки
FULL_SO_PATH="$LIB_PATH/Libs/linux64"
echo "Найден путь к библиотекам: $FULL_SO_PATH"

# 4. Устанавливаем переменную LD_LIBRARY_PATH, чтобы система нашла все .so файлы
export LD_LIBRARY_PATH=$FULL_SO_PATH:$LD_LIBRARY_PATH

# 5. Запускаем ваш основной скрипт
echo "Запуск скрипта добавления лица..."
python3 create_face_user.py