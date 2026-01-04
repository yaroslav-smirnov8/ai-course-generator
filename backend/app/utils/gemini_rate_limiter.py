"""
Модуль для управления лимитами API Google Gemini и ротацией ключей.

Предоставляет функциональность для:
1. Автоматического переключения между моделями Gemini при достижении лимитов
2. Ротации ключей API при необходимости
3. Отслеживания использования API и ошибок
"""

import os
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

class APIKeyManager:
    """Управление набором ключей API"""
    
    def __init__(self):
        """Инициализирует менеджер ключей API"""
        # Получаем основной ключ API
        main_key = os.getenv("GEMINI_API_KEY", "")
        
        # Получаем дополнительные ключи API
        extra_keys_str = os.getenv("GEMINI_EXTRA_API_KEYS", "")
        extra_keys = [k.strip() for k in extra_keys_str.split(",") if k.strip()]
        
        # Объединяем все ключи
        self.all_keys = [main_key] + extra_keys if main_key else extra_keys
        self.all_keys = [key for key in self.all_keys if key]  # Убираем пустые ключи
        
        # Включение ротации ключей
        self.enable_rotation = os.getenv("ENABLE_KEY_ROTATION", "false").lower() == "true"
        
        logger.info(f"Инициализирован менеджер ключей API. Доступно ключей: {len(self.all_keys)}")
        logger.info(f"Ротация ключей: {'включена' if self.enable_rotation else 'выключена'}")
    
    def get_available_key(self, used_keys: List[str] = None) -> Optional[str]:
        """
        Возвращает доступный ключ API, который ещё не использовался
        
        Args:
            used_keys: Список уже использованных ключей
            
        Returns:
            Доступный ключ API или None, если все ключи уже использованы
        """
        if not self.all_keys:
            logger.warning("Нет доступных ключей API")
            return None
        
        if not used_keys:
            # Если список использованных ключей не предоставлен, возвращаем первый ключ
            return self.all_keys[0]
        
        if not self.enable_rotation:
            # Если ротация ключей отключена, возвращаем первый ключ независимо от его использования
            return self.all_keys[0]
        
        # Ищем первый ключ, который ещё не использовался
        for key in self.all_keys:
            if key not in used_keys:
                return key
        
        # Если все ключи уже использовались, возвращаем None
        return None


class GeminiRateLimiter:
    """Менеджер лимитов API Google Gemini"""
    
    def __init__(self):
        """Инициализирует менеджер лимитов API"""
        # Лимиты для каждой модели (requests per minute, requests per day, tokens per minute)
        self.model_limits = {
            "gemini-2.0-flash": {"rpm": 15, "rpd": 1500, "tpm": 60000},
            "gemini-1.5-flash": {"rpm": 15, "rpd": 1500, "tpm": 60000},
            "gemini-1.5-pro": {"rpm": 2, "rpd": 50, "tpm": 20000}
        }
        
        # Приоритет моделей (от самой предпочтительной к наименее предпочтительной)
        self.model_priority = {
            "gemini-2.0-flash": 1,  # Наивысший приоритет
            "gemini-1.5-flash": 2,
            "gemini-1.5-pro": 3    # Низший приоритет
        }
        
        # Получаем переменные окружения
        self.default_model = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.0-flash")
        self.enable_model_fallback = os.getenv("ENABLE_MODEL_FALLBACK", "true").lower() == "true"
        self.usage_reset_interval = int(os.getenv("USAGE_RESET_INTERVAL", "86400"))  # 24 часа по умолчанию
        self.enabled = os.getenv("USE_RATE_LIMITER", "true").lower() == "true"
        
        # Инициализируем менеджер ключей
        self.key_manager = APIKeyManager()
        
        # Отслеживание использования API
        # Формат: {ключ: {модель: {"minute_count": 0, "day_count": 0, "minute_start": timestamp, "day_start": timestamp, "errors": 0}}}
        self.usage = {}
        
        # Инициализируем отслеживание использования для всех ключей и моделей
        self.init_usage_tracking()
        
        # Запускаем фоновый поток для периодического сброса статистики использования
        self.start_reset_thread()
        
        logger.info(f"Инициализирован менеджер лимитов API Gemini. Активирован: {self.enabled}")
        logger.info(f"Модель по умолчанию: {self.default_model}")
        logger.info(f"Автоматическое переключение моделей: {'включено' if self.enable_model_fallback else 'выключено'}")
    
    def init_usage_tracking(self):
        """Инициализирует отслеживание использования для всех ключей и моделей"""
        now = time.time()
        
        for key in self.key_manager.all_keys:
            if key not in self.usage:
                self.usage[key] = {}
                
            for model in self.model_limits.keys():
                if model not in self.usage[key]:
                    self.usage[key][model] = {
                        "minute_count": 0,
                        "day_count": 0,
                        "errors": 0,
                        "minute_start": now,
                        "day_start": now
                    }
    
    def start_reset_thread(self):
        """Запускает фоновый поток для периодического сброса статистики использования"""
        if not self.enabled:
            return
            
        def reset_worker():
            while True:
                # Ждем указанный интервал
                time.sleep(self.usage_reset_interval)
                # Сбрасываем статистику
                self.reset_daily_usage()
                logger.info(f"Выполнен автоматический сброс статистики использования API")
        
        # Запускаем поток как демон, чтобы он автоматически завершался при завершении основного потока
        thread = threading.Thread(target=reset_worker, daemon=True)
        thread.start()
        logger.info(f"Запущен фоновый поток для сброса статистики. Интервал: {self.usage_reset_interval} сек.")
    
    def reset_daily_usage(self):
        """Сбрасывает дневную статистику использования для всех ключей и моделей"""
        now = time.time()
        
        for key in self.usage:
            for model in self.usage[key]:
                self.usage[key][model]["day_count"] = 0
                self.usage[key][model]["day_start"] = now
                
                # Также проверяем, не прошла ли минута с момента последнего запроса
                if now - self.usage[key][model]["minute_start"] >= 60:
                    self.usage[key][model]["minute_count"] = 0
                    self.usage[key][model]["minute_start"] = now
    
    def record_usage(self, api_key: str, model: str):
        """
        Записывает использование API
        
        Args:
            api_key: Ключ API
            model: Название модели
        """
        if not self.enabled or api_key not in self.usage:
            return
            
        if model not in self.usage[api_key]:
            # Инициализируем отслеживание для новой модели
            self.usage[api_key][model] = {
                "minute_count": 0,
                "day_count": 0,
                "errors": 0,
                "minute_start": time.time(),
                "day_start": time.time()
            }
        
        now = time.time()
        
        # Проверяем, не прошла ли минута с момента последнего запроса
        if now - self.usage[api_key][model]["minute_start"] >= 60:
            self.usage[api_key][model]["minute_count"] = 0
            self.usage[api_key][model]["minute_start"] = now
        
        # Увеличиваем счетчики использования
        self.usage[api_key][model]["minute_count"] += 1
        self.usage[api_key][model]["day_count"] += 1
        
        # Проверяем, не превышены ли лимиты
        rpm_limit = self.model_limits[model]["rpm"]
        rpd_limit = self.model_limits[model]["rpd"]
        
        minute_usage = self.usage[api_key][model]["minute_count"]
        day_usage = self.usage[api_key][model]["day_count"]
        
        if minute_usage >= rpm_limit:
            logger.warning(f"Достигнут лимит запросов в минуту ({rpm_limit}) для модели {model} и ключа {api_key[:5]}...")
            
        if day_usage >= rpd_limit:
            logger.warning(f"Достигнут лимит запросов в день ({rpd_limit}) для модели {model} и ключа {api_key[:5]}...")
    
    def record_error(self, api_key: str, model: str, error_details: str = ""):
        """
        Записывает ошибку при использовании API
        
        Args:
            api_key: Ключ API
            model: Название модели
            error_details: Детали ошибки
        """
        if not self.enabled or api_key not in self.usage:
            return
            
        if model not in self.usage[api_key]:
            # Инициализируем отслеживание для новой модели
            self.usage[api_key][model] = {
                "minute_count": 0,
                "day_count": 0,
                "errors": 0,
                "minute_start": time.time(),
                "day_start": time.time()
            }
        
        # Увеличиваем счетчик ошибок
        self.usage[api_key][model]["errors"] += 1
        
        logger.error(f"Ошибка при использовании модели {model} с ключом {api_key[:5]}...: {error_details}")
    
    def is_key_available(self, api_key: str, model: str) -> bool:
        """
        Проверяет, доступен ли указанный ключ API для использования с указанной моделью
        
        Args:
            api_key: Ключ API
            model: Название модели
            
        Returns:
            True, если ключ доступен, иначе False
        """
        if not self.enabled or api_key not in self.usage:
            return True
            
        if model not in self.usage[api_key]:
            return True
        
        now = time.time()
        
        # Проверяем, не прошла ли минута с момента последнего запроса
        if now - self.usage[api_key][model]["minute_start"] >= 60:
            self.usage[api_key][model]["minute_count"] = 0
            self.usage[api_key][model]["minute_start"] = now
            return True
        
        # Проверяем лимиты
        rpm_limit = self.model_limits[model]["rpm"]
        rpd_limit = self.model_limits[model]["rpd"]
        
        minute_usage = self.usage[api_key][model]["minute_count"]
        day_usage = self.usage[api_key][model]["day_count"]
        
        return minute_usage < rpm_limit and day_usage < rpd_limit
    
    def get_available_model(self, api_key: str) -> Optional[str]:
        """
        Возвращает доступную модель для указанного ключа API
        
        Args:
            api_key: Ключ API
            
        Returns:
            Название доступной модели или None, если все модели недоступны
        """
        if not self.enabled:
            return self.default_model
            
        if not self.enable_model_fallback:
            # Если переключение моделей отключено, возвращаем модель по умолчанию
            return self.default_model
        
        # Сортируем модели по приоритету
        sorted_models = sorted(self.model_priority.items(), key=lambda x: x[1])
        
        # Проверяем каждую модель, начиная с самой приоритетной
        for model, _ in sorted_models:
            if self.is_key_available(api_key, model):
                return model
        
        # Если все модели недоступны, возвращаем None
        return None
    
    def get_available_key_and_model(self) -> Tuple[str, str]:
        """
        Возвращает доступные ключ API и модель
        
        Returns:
            Кортеж (ключ API, название модели)
        """
        if not self.enabled:
            # Если менеджер лимитов отключен, возвращаем первый ключ и модель по умолчанию
            return self.key_manager.all_keys[0] if self.key_manager.all_keys else "", self.default_model
        
        used_keys = []
        
        # Проверяем каждый ключ
        for _ in range(len(self.key_manager.all_keys)):
            # Получаем доступный ключ
            api_key = self.key_manager.get_available_key(used_keys)
            
            if not api_key:
                # Если все ключи уже проверены, возвращаем первый ключ и модель по умолчанию
                logger.warning("Все ключи уже были проверены, возвращаем первый ключ")
                return self.key_manager.all_keys[0] if self.key_manager.all_keys else "", self.default_model
            
            # Добавляем ключ в список использованных
            used_keys.append(api_key)
            
            # Получаем доступную модель для этого ключа
            model = self.get_available_model(api_key)
            
            if model:
                return api_key, model
        
        # Если не найдено доступных ключей и моделей, возвращаем первый ключ и модель по умолчанию
        logger.warning("Не найдено доступных ключей и моделей, возвращаем значения по умолчанию")
        return self.key_manager.all_keys[0] if self.key_manager.all_keys else "", self.default_model
    
    def get_usage_stats(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Возвращает статистику использования API
        
        Returns:
            Словарь со статистикой использования для всех ключей и моделей
        """
        return self.usage
    
    def increment_usage(self, api_key: str, model: str, count: int = 1):
        """
        Увеличивает счетчик использования API на указанное количество
        
        Args:
            api_key: Ключ API
            model: Название модели
            count: Количество запросов для добавления
        """
        if not self.enabled or api_key not in self.usage:
            return
            
        if model not in self.usage[api_key]:
            # Инициализируем отслеживание для новой модели
            self.usage[api_key][model] = {
                "minute_count": 0,
                "day_count": 0,
                "errors": 0,
                "minute_start": time.time(),
                "day_start": time.time()
            }
        
        # Увеличиваем счетчики использования
        self.usage[api_key][model]["minute_count"] += count
        self.usage[api_key][model]["day_count"] += count
        
        # Логируем информацию о превышении лимитов
        rpm_limit = self.model_limits[model]["rpm"]
        rpd_limit = self.model_limits[model]["rpd"]
        
        minute_usage = self.usage[api_key][model]["minute_count"]
        day_usage = self.usage[api_key][model]["day_count"]
        
        if minute_usage >= rpm_limit:
            logger.warning(f"Достигнут лимит запросов в минуту ({rpm_limit}) для модели {model} и ключа {api_key[:5]}...")
            
        if day_usage >= rpd_limit:
            logger.warning(f"Достигнут лимит запросов в день ({rpd_limit}) для модели {model} и ключа {api_key[:5]}...")
    
    def reload_settings(self):
        """
        Перезагружает настройки из переменных окружения
        """
        # Обновляем настройки из переменных окружения
        self.default_model = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.0-flash")
        self.enable_model_fallback = os.getenv("ENABLE_MODEL_FALLBACK", "true").lower() == "true"
        self.usage_reset_interval = int(os.getenv("USAGE_RESET_INTERVAL", "86400"))
        self.enabled = os.getenv("USE_RATE_LIMITER", "true").lower() == "true"
        
        # Обновляем настройки менеджера ключей
        self.key_manager.enable_rotation = os.getenv("ENABLE_KEY_ROTATION", "false").lower() == "true"
        
        # Обновляем список ключей
        main_key = os.getenv("GEMINI_API_KEY", "")
        extra_keys_str = os.getenv("GEMINI_EXTRA_API_KEYS", "")
        extra_keys = [k.strip() for k in extra_keys_str.split(",") if k.strip()]
        
        self.key_manager.all_keys = [main_key] + extra_keys if main_key else extra_keys
        self.key_manager.all_keys = [key for key in self.key_manager.all_keys if key]
        
        # Заново инициализируем отслеживание использования
        self.init_usage_tracking()
        
        logger.info(f"Настройки менеджера лимитов обновлены")
        logger.info(f"Ротация ключей: {'включена' if self.key_manager.enable_rotation else 'выключена'}")
        logger.info(f"Переключение моделей: {'включено' if self.enable_model_fallback else 'выключено'}")

# Создаем глобальный экземпляр менеджера лимитов
gemini_limiter = GeminiRateLimiter() 