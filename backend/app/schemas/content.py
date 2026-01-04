from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from ..core.constants import ContentType
from .base import BaseSchema

class ApiResponse(BaseSchema):
    """Базовая схема ответа API"""
    status: str = Field(default="success")
    message: Optional[str] = None

class GenerationStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"

class GenerationBase(BaseSchema):
    """Базовая схема для генерации контента"""
    user_id: int
    type: Union[ContentType, str]  # Accept either ContentType enum or string
    prompt: str

    @validator('type')
    def validate_type(cls, v):
        # If v is a string, try to convert it to ContentType
        if isinstance(v, str):
            try:
                return ContentType(v)
            except ValueError:
                raise ValueError(f"Invalid content type: {v}")
        return v

class ContentGenerationBase(GenerationBase):
    """Базовая схема для запроса генерации контента"""
    pass

class ContentGeneration(ContentGenerationBase):
    """Схема для запроса генерации контента"""
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")

class GeneratedContent(GenerationBase):
    """Схема сгенерированного контента"""
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# Схемы для анализатора текста
class TextAnalyzerBase(BaseSchema):
    """Базовая схема для анализатора текста"""
    user_id: int
    language: str = Field(min_length=2, max_length=50)
    text_content: str = Field(min_length=1)
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")

class DetectTextLevelRequest(TextAnalyzerBase):
    """Схема для запроса определения уровня текста"""
    pass

class RegenerateTextRequest(TextAnalyzerBase):
    """Схема для запроса перегенерации текста"""
    vocabulary: str = Field(default="neutral")
    preserve_style: bool = Field(default=False, description="Сохранять ли стиль текста при перегенерации")
    style: str = Field(default="neutral", description="Стиль текста после регенерации")

class ChangeTextLevelRequest(TextAnalyzerBase):
    """Схема для запроса изменения уровня текста"""
    target_level: str
    preserve_style: bool = Field(default=False, description="Сохранять ли стиль текста при изменении уровня")
    vocabulary: str = Field(default="neutral", description="Тип словарного запаса для текста")
    style: str = Field(default="neutral", description="Стиль текста после адаптации")

class GenerateQuestionsRequest(TextAnalyzerBase):
    """Схема для запроса генерации вопросов к тексту"""
    count: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="medium")
    vocabulary: Optional[str] = Field(default=None, description="Целевая лексика. Если None, будет определена автоматически из текста")
    grammar: Optional[str] = Field(default=None, description="Целевая грамматика. Если None, будет определена автоматически из текста")
    topic: Optional[str] = Field(default="text_questions", description="Тема вопросов. По умолчанию используется 'text_questions'")
    force: bool = Field(default=False, description="Принудительно сгенерировать новые вопросы, игнорируя кэш")

class GenerateSummaryRequest(TextAnalyzerBase):
    """Схема для запроса генерации саммари текста"""
    max_length: Optional[int] = Field(default=None, ge=50, le=500, description="Максимальная длина саммари в словах (не в символах)")
    level: Optional[str] = Field(default=None, description="Уровень владения языком для генерации саммари (например, 'a1', 'b2', 'c1' для CEFR)")

class GenerateTitlesRequest(TextAnalyzerBase):
    """Схема для запроса генерации названий для текста"""
    count: int = Field(default=4, ge=1, le=10)
    force: bool = Field(default=False, description="Принудительно сгенерировать новые заголовки, игнорируя кэш")

class GenerateComprehensionTestRequest(TextAnalyzerBase):
    """Схема для запроса генерации теста на понимание текста"""
    question_count: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="medium")
    force: bool = Field(default=False, description="Принудительно сгенерировать новый тест, игнорируя кэш")

class TextAnalyzerResponse(ApiResponse):
    """Схема ответа анализатора текста"""
    data: Dict[str, Any]

    class Config:
        from_attributes = True

class ImageBase(BaseSchema):
    """Базовая схема для изображения"""
    user_id: int
    prompt: str

class ImageGenerationRequest(ImageBase):
    """Схема запроса генерации изображения"""
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")
    use_cache: bool = Field(default=True, description="Использовать кэширование для генерации изображений")

class ImageResponseData(BaseSchema):
    """Схема данных ответа с изображением"""
    id: int
    url: str
    created_at: datetime

class VideoTranscriptBase(BaseSchema):
    """Базовая схема для транскрипта видео"""
    user_id: int
    video_id: str
    subtitle_language: str = Field(
        default="en",
        description="Language code for subtitles",
        min_length=2,
        max_length=10
    )

    @validator('subtitle_language')
    def validate_language(cls, v):
        if not v.isalpha():
            raise ValueError('Language code must contain only letters')
        return v.lower()

class VideoTranscriptRequest(VideoTranscriptBase):
    """Схема запроса транскрипта видео"""
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")

class VideoTranscriptData(BaseSchema):
    """Схема данных транскрипта"""
    id: int
    transcript: str
    language: str
    created_at: datetime
    expires_at: datetime

class TranscriptSettings(BaseSchema):
    """Базовые настройки для работы с транскриптом"""
    language: str
    topic: str
    age: str = Field(default="adults")
    individual_group: str = Field(default="individual")
    online_offline: str = Field(default="online")

class TranscriptContentGeneration(VideoTranscriptBase, TranscriptSettings):
    """Схема для генерации контента на основе транскрипта"""
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")

class ExerciseSettings(BaseSchema):
    """Настройки для генерации упражнений"""
    difficulty: str = Field(default="medium")
    exercise_type: str = Field(default="grammar")
    quantity: int = Field(default=3, ge=1, le=10)

class GameSettings(BaseSchema):
    """Настройки для генерации игр"""
    game_type: str = Field(default="language")
    duration: int = Field(default=15, ge=5, le=60)

class ExerciseFromTranscriptRequest(TranscriptContentGeneration, ExerciseSettings):
    """Схема для запроса генерации упражнений из транскрипта"""
    pass

class GameFromTranscriptRequest(TranscriptContentGeneration, GameSettings):
    """Схема для запроса генерации игр из транскрипта"""
    pass

class BaseTranscriptGeneration(BaseSchema):
    """Базовая схема для генерации на основе транскрипта"""
    user_id: int
    video_id: str
    language: str = Field(min_length=2, max_length=10)
    topic: str
    with_points: bool = Field(default=False, description="Использовать баллы для генерации вместо дневных лимитов")
    skip_tariff_check: bool = Field(default=False, description="Пропустить проверку тарифа")
    skip_limits: bool = Field(default=False, description="Пропустить проверку лимитов")

class ExerciseTranscriptGeneration(BaseTranscriptGeneration, ExerciseSettings):
    """Схема для генерации упражнений из транскрипта"""
    pass

class GameTranscriptGeneration(BaseTranscriptGeneration, GameSettings):
    """Схема для генерации игр из транскрипта"""
    pass

class LessonPlanTranscriptGeneration(BaseTranscriptGeneration, TranscriptSettings):
    """Схема для генерации плана урока из транскрипта"""
    pass

class ContentResponse(ApiResponse):
    """Схема ответа с контентом"""
    data: Dict[str, Any]
    with_points: bool = Field(default=False, description="Использовались ли баллы для генерации")

    class Config:
        from_attributes = True

class ImageResponse(ApiResponse):
    """Схема ответа с изображением"""
    data: Dict[str, Any]

    class Config:
        from_attributes = True

class VideoTranscriptResponse(ApiResponse):
    """Схема ответа с транскриптом"""
    data: Dict[str, Any]

    class Config:
        from_attributes = True

class ErrorResponse(BaseSchema):
    """Схема ответа с ошибкой"""
    status: str = Field(default="error")
    detail: str
    code: Optional[str] = None

    class Config:
        from_attributes = True

class G4FStatusResponse(BaseSchema):
    """Схема ответа о статусе G4FHandler"""
    available: bool
    model: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None

class G4FUpdateParams(BaseSchema):
    """Схема параметров для обновления G4FHandler"""
    timeout: Optional[int] = None
    force_refresh: bool = Field(default=False)
    clear_cache: bool = Field(default=False)
    content_type: Optional[str] = None

class TextLevelAnalysis(BaseSchema):
    """Класс для хранения результатов анализа уровня текста"""
    level: str
    markdown_content: str
    raw_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для совместимости"""
        return {
            "level": self.level,
            "markdown_content": self.markdown_content,
            "raw_analysis": self.raw_analysis
        }

class TitlesAnalysis(BaseSchema):
    """Класс для хранения результатов генерации заголовков"""
    titles: List[str]
    recommended_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для совместимости"""
        return {
            "titles": self.titles,
            "recommended_index": self.recommended_index
        }

class QuestionsAnalysis(BaseSchema):
    """Класс для хранения результатов генерации вопросов"""
    questions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для совместимости"""
        return {
            "questions": self.questions
        }