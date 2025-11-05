FROM python:3.9-slim

WORKDIR /app

COPY src/dahua_sdk/Libs/linux64 /app/src/dahua_sdk/Libs/linux64

ENV LD_LIBRARY_PATH=/app/src/dahua_sdk/Libs/linux64

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Указываем команду для запуска приложения
CMD ["python", "src/main.py"]