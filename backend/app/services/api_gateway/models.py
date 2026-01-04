"""
Модели данных для API Gateway
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ProviderType(Enum):
    """Provider types"""
    DIRECT = "direct"
    NETLIFY = "netlify"
    CUSTOM = "custom"


class ContentType(Enum):
    """Типы контента"""
    TEXT = "text"
    IMAGE = "image"


class ModelStatus(Enum):
    """Статус модели"""
    AVAILABLE = "available"
    COOLDOWN = "cooldown"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ModelConfig:
    """Конфигурация модели"""
    name: str
    provider_type: str  # gemini, groq, openrouter, llm7, together, etc.
    api_url: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60
    retry_count: int = 2
    cooldown_minutes: int = 5
    priority: int = 0  # Чем меньше, тем выше приоритет
    
    # Специфичные параметры для разных провайдеров
    request_format: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Статус модели
    status: ModelStatus = ModelStatus.AVAILABLE
    cooldown_until: Optional[datetime] = None
    error_count: int = 0
    last_success: Optional[datetime] = None


@dataclass
class ProviderConfig:
    """Конфигурация провайдера"""
    name: str
    type: ProviderType
    priority: int  # Чем меньше, тем выше приоритет
    enabled: bool = True
    
    # Модели, поддерживаемые провайдером
    models: List[ModelConfig] = field(default_factory=list)
    
    # Настройки провайдера
    base_url: Optional[str] = None
    timeout: int = 300
    retry_count: int = 2
    max_concurrent_requests: int = 10
    
    # Эндпоинты для разных типов контента
    endpoints: Dict[str, str] = field(default_factory=dict)
    
    # Additional configuration for custom providers
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    # Статистика
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_request: Optional[datetime] = None
    
    def get_success_rate(self) -> float:
        """Получить процент успешных запросов"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_available_models(self) -> List[ModelConfig]:
        """Получить доступные модели (не в cooldown и не с ошибками)"""
        now = datetime.utcnow()
        available = []
        
        for model in self.models:
            if model.status == ModelStatus.DISABLED:
                continue
                
            if model.status == ModelStatus.COOLDOWN and model.cooldown_until:
                if now < model.cooldown_until:
                    continue
                else:
                    # Cooldown истек, возвращаем модель в доступные
                    model.status = ModelStatus.AVAILABLE
                    model.cooldown_until = None
            
            available.append(model)
        
        # Сортируем по приоритету
        return sorted(available, key=lambda m: m.priority)


@dataclass
class APIRequest:
    """Запрос к API"""
    endpoint: str
    content_type: ContentType
    data: Dict[str, Any]
    api_keys: Dict[str, str]
    
    # Опциональные параметры
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    
    # Метаданные
    request_id: str = field(default_factory=lambda: f"req_{datetime.utcnow().timestamp()}")
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIResponse:
    """Ответ от API"""
    success: bool
    content: str = ""
    
    # Метаданные о выполнении
    provider_name: str = ""
    model_name: str = ""
    response_time: float = 0.0
    tokens_used: int = 0
    
    # Дополнительные данные
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Ошибки
    error: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Для изображений
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    
    # Временные метки
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для JSON ответа"""
        result = {
            'success': self.success,
            'content': self.content,
            'provider': self.provider_name,
            'model': self.model_name,
            'response_time': self.response_time,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata
        }
        
        if self.error:
            result['error'] = self.error
            result['error_details'] = self.error_details
            
        if self.image_url:
            result['image_url'] = self.image_url
            
        return result


@dataclass
class ProviderStats:
    """Статистика провайдера"""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_tokens_used: int = 0
    
    # Статистика по моделям
    model_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Временные метки
    first_request: Optional[datetime] = None
    last_request: Optional[datetime] = None
    
    def update_stats(self, response: APIResponse):
        """Обновить статистику на основе ответа"""
        self.total_requests += 1
        self.last_request = datetime.utcnow()
        
        if self.first_request is None:
            self.first_request = self.last_request
        
        if response.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Обновляем среднее время ответа
        if self.total_requests == 1:
            self.average_response_time = response.response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1) + response.response_time) 
                / self.total_requests
            )
        
        self.total_tokens_used += response.tokens_used
        
        # Статистика по модели
        model_name = response.model_name
        if model_name not in self.model_stats:
            self.model_stats[model_name] = {
                'requests': 0,
                'successes': 0,
                'failures': 0,
                'avg_response_time': 0.0,
                'tokens_used': 0
            }
        
        model_stat = self.model_stats[model_name]
        model_stat['requests'] += 1
        
        if response.success:
            model_stat['successes'] += 1
        else:
            model_stat['failures'] += 1
        
        # Обновляем среднее время для модели
        if model_stat['requests'] == 1:
            model_stat['avg_response_time'] = response.response_time
        else:
            model_stat['avg_response_time'] = (
                (model_stat['avg_response_time'] * (model_stat['requests'] - 1) + response.response_time)
                / model_stat['requests']
            )
        
        model_stat['tokens_used'] += response.tokens_used
    
    def get_success_rate(self) -> float:
        """Получить процент успешных запросов"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
