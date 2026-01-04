import logging
import os
from logging.handlers import RotatingFileHandler

def setup_g4f_logging():
    """Настраивает логирование для модуля g4f"""
    # Создаем путь к директории logs
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'g4f.log')
    
    # Настройка логгера для g4f
    g4f_logger = logging.getLogger('g4f')
    g4f_logger.setLevel(logging.DEBUG)
    
    # Проверяем, есть ли уже обработчики, чтобы избежать дублирования
    if not g4f_logger.handlers:
        # Добавляем обработчик для записи в отдельный файл с ротацией (максимальный размер файла 10MB, до 5 файлов бэкапа)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
        file_handler.setFormatter(formatter)
        g4f_logger.addHandler(file_handler)
        
        # Также добавляем обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        g4f_logger.addHandler(console_handler)
    
    return g4f_logger

def get_g4f_logger(name='g4f'):
    """Получает настроенный логгер для g4f с указанным именем"""
    setup_g4f_logging()
    return logging.getLogger(name) 