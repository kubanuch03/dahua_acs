# src/utils/config.py

import os
from dotenv import load_dotenv

load_dotenv()

config = {
    'event_source_device': {
        'ip': os.environ.get('DAHUA_EVENT_IP'),
        'port': int(os.environ.get('DAHUA_EVENT_PORT', 37777)),
        'user': os.environ.get('DAHUA_EVENT_USER'),
        'password': os.environ.get('DAHUA_EVENT_PASSWORD')
    },
    'command_target_controller': {
        'ip': os.environ.get('DAHUA_CONTROLLER_IP'),
        'port': int(os.environ.get('DAHUA_CONTROLLER_PORT', 37777)),
        'user': os.environ.get('DAHUA_CONTROLLER_USER'),
        'password': os.environ.get('DAHUA_CONTROLLER_PASSWORD')
    },
    'api_server': {
        'host': os.environ.get('API_HOST', '0.0.0.0'),
        'port': int(os.environ.get('API_PORT', 8000))
    },
    'logging': {
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
        'file_path': os.environ.get('LOG_FILE_PATH', 'app.log')
    },
    'redis': {
        'host': os.environ.get('REDIS_HOST', 'redis'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0)),
        'password': str(os.environ.get('REDIS_PASSWORD', 0)),
        
    },
    
}

 