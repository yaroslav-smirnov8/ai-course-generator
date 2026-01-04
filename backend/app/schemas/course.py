from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.constants import CourseLevel, CourseFormat, TargetAudience
from .base import BaseSchema


class ActivityBase(BaseSchema):
    """Базовая схема активности"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
    duration: int = Field(..., gt=0)
    description: Optional[str] = None
    materials: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)


class ActivityCreate(ActivityBase):
    """Схема для создания активности"""
    pass


class Activity(ActivityBase):
    """Полная схема активности"""
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Схемы для генерации упражнений ---

class LessonContextForGeneration(BaseModel):
    """Детали урока для передачи в генератор"""
    title: str
    objectives: List[str] = Field(default_factory=list)
    grammar: List[str] = Field(default_factory=list)
    vocabulary: List[str] = Field(default_factory=list)
    duration: Optional[int] = None
    # Можно добавить другие поля урока при необходимости

class CourseContextForGeneration(BaseModel):
    """Контекст курса для передачи в генератор"""
    language: str
    level: CourseLevel
    target_audience: TargetAudience
    methodology: Optional[str] = None
    age: Optional[str] = None # Используем student_age из CourseBase
    goals: Optional[str] = None # Используем student_goals из CourseBase
    interests: Optional[str] = None # Используем student_interests из CourseBase
    # Можно добавить другие поля курса при необходимости

class GenerateExercisesRequest(BaseModel):
    """Схема запроса для генерации упражнений"""
    lesson_details: LessonContextForGeneration
    course_context: CourseContextForGeneration

class GeneratedExercisesResponse(BaseModel):
    """Схема ответа с сгенерированными упражнениями"""
    exercises_content: str = Field(..., description="Сгенерированные упражнения в формате Markdown")
    processed_exercises: Optional[List[Dict[str, Any]]] = Field(default=None, description="Обработанные упражнения в структурированном формате")

# --- Конец схем для генерации упражнений ---


# --- Схемы для генерации игр ---

class GenerateGameRequest(BaseModel):
    """Схема запроса для генерации игры"""
    lesson_details: LessonContextForGeneration # Используем ту же схему деталей урока
    course_context: CourseContextForGeneration # Используем ту же схему контекста курса
    game_type: Optional[str] = Field(None, description="Предпочтительный тип игры (e.g., matching, quiz, crossword)")

class GeneratedGameResponse(BaseModel):
    """Схема ответа с сгенерированной игрой"""
    game_content: str = Field(..., description="Сгенерированное описание/правила игры в формате Markdown")
    game_type: Optional[str] = Field(None, description="Тип сгенерированной игры (если определен AI)")
    processed_game: Optional[Dict[str, Any]] = Field(default=None, description="Обработанная игра в структурированном формате")

# --- Конец схем для генерации игр ---


# --- Схемы для генерации упражнений ---

class LessonContextForGeneration(BaseModel):
    """Детали урока для передачи в генератор"""
    title: str
    objectives: List[str] = Field(default_factory=list)
    grammar: List[str] = Field(default_factory=list)
    vocabulary: List[str] = Field(default_factory=list)
    duration: Optional[int] = None
    # Можно добавить другие поля урока при необходимости

class CourseContextForGeneration(BaseModel):
    """Контекст курса для передачи в генератор"""
    language: str
    level: CourseLevel
    target_audience: TargetAudience
    methodology: Optional[str] = None
    age: Optional[str] = None # Используем student_age из CourseBase
    goals: Optional[str] = None # Используем student_goals из CourseBase
    interests: Optional[str] = None # Используем student_interests из CourseBase
    # Можно добавить другие поля курса при необходимости


class LessonBase(BaseSchema):
    """Базовая схема урока"""
    title: str = Field(..., min_length=1, max_length=255)
    duration: int = Field(..., gt=0)
    order: int = Field(..., ge=0)
    objectives: List[str] = Field(default_factory=list)
    grammar: List[str] = Field(default_factory=list)
    vocabulary: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    homework: Dict[str, Any] = Field(default_factory=dict)

    @validator('duration')
    def validate_duration(cls, v):
        if v > 180:  # 3 часа
            raise ValueError('Duration cannot exceed 180 minutes')
        return v


class LessonCreate(LessonBase):
    """Схема для создания урока"""
    activities: List[ActivityCreate] = Field(default_factory=list)


class Lesson(LessonBase):
    """Полная схема урока"""
    id: int
    course_id: int
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    activities: List[Activity] = []
    plan_content: Optional[str] = None # <-- Добавлено поле для плана урока

    class Config:
        from_attributes = True


# --- Схемы для материалов урока ---

class ExerciseMaterial(BaseModel):
    """Схема для упражнения"""
    type: str = Field("exercise", description="Тип материала")
    title: str = Field(..., description="Название упражнения")
    content_md: str = Field(..., description="Содержимое упражнения в формате Markdown")
    answers_md: Optional[str] = Field(None, description="Ответы в формате Markdown, если применимо")

class HandoutMaterial(BaseModel):
    """Схема для раздаточного материала"""
    type: str = Field(..., description="Тип раздатки (summary, worksheet, vocabulary, grammar)")
    title: str = Field(..., description="Название материала")
    content_md: str = Field(..., description="Содержимое в Markdown")
    pages: Optional[int] = Field(None, description="Примерное количество страниц")

class PresentationSlide(BaseModel):
    """Схема для слайда презентации"""
    type: str = Field(..., description="Тип слайда (title, content, exercise, summary, quiz)")
    content: Dict[str, Any] = Field(..., description="Структурированное содержимое слайда")
    notes: Optional[str] = Field(None, description="Заметки для спикера")

class PresentationMaterial(BaseModel):
    """Схема для презентации"""
    type: str = Field("presentation", description="Тип материала")
    title: str = Field(..., description="Название презентации")
    slides: List[PresentationSlide] = Field(default_factory=list, description="Список слайдов")
    theme: Optional[str] = Field("default", description="Тема оформления")

class LessonMaterialsResponse(BaseModel):
    """Схема ответа с материалами урока"""
    lesson_id: int
    exercises: Optional[List[ExerciseMaterial]] = Field(None, description="Сгенерированные упражнения")
    presentation: Optional[PresentationMaterial] = Field(None, description="Сгенерированная презентация")
    handouts: Optional[List[HandoutMaterial]] = Field(None, description="Сгенерированные раздаточные материалы")
    # Можно добавить другие типы материалов (assessments и т.д.)
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Время генерации материалов")

    class Config:
        from_attributes = True # Если нужно будет возвращать объекты ORM

# --- Конец схем для материалов урока ---


class CourseBase(BaseSchema):
    """Базовая схема курса"""
    name: str = Field(..., min_length=1, max_length=255)
    language: str = Field(..., min_length=2, max_length=50)
    level: CourseLevel
    start_level: Optional[CourseLevel] = None
    target_audience: TargetAudience
    format: CourseFormat
    description: Optional[str] = None
    exam_prep: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)

    # Методика и структура
    methodology: Optional[str] = None
    lessons_count: Optional[int] = Field(None, ge=1, le=30)
    lesson_duration: Optional[int] = Field(None, ge=30, le=180)

    # Фокус курса
    main_topics: Optional[str] = None
    grammar_focus: Optional[str] = None
    vocabulary_focus: Optional[str] = None

    # Информация о студенте
    student_age: Optional[str] = None
    student_interests: Optional[str] = None
    student_goals: Optional[str] = None
    common_mistakes: Optional[str] = None

    # Включаемые навыки
    include_speaking: bool = True
    include_listening: bool = True
    include_reading: bool = True
    include_writing: bool = True
    include_games: bool = True

    # Расширенная информация о подготовке к экзамену
    custom_exam: Optional[str] = None
    exam_prep_lessons: Optional[int] = Field(None, ge=0)

    @validator('language')
    def validate_language(cls, v):
        return v.lower()


class CourseCreate(CourseBase):
    """Схема для создания курса"""
    lessons: List[LessonCreate] = Field(default_factory=list)

    # Дополнительные поля для генерации за баллы
    with_points: Optional[bool] = Field(None, description="Флаг генерации за баллы")
    skip_tariff_check: Optional[bool] = Field(None, description="Флаг пропуска проверки тарифа")
    skip_limits: Optional[bool] = Field(None, description="Флаг пропуска проверки лимитов")

    @validator('lessons')
    def validate_lessons(cls, v, values):
        if 'lessons_count' in values and values['lessons_count'] and values['lessons_count'] > 0:
            return v
        if not v:
            raise ValueError('Course must have at least one lesson')
        return v


class CourseUpdate(BaseSchema):
    """Схема для обновления курса"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    language: Optional[str] = Field(None, min_length=2, max_length=50)
    level: Optional[CourseLevel] = None
    target_audience: Optional[TargetAudience] = None
    format: Optional[CourseFormat] = None
    description: Optional[str] = None
    exam_prep: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    learning_outcomes: Optional[List[str]] = None

    def model_dump(self, **kwargs):
        """Переопределяем метод model_dump для совместимости с Pydantic v1"""
        return super().model_dump(**kwargs)


class Course(CourseBase):
    """Полная схема курса"""
    id: int
    total_duration: int
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    lessons: List[Lesson] = []

    # Дополнительные поля
    progress: Optional[float] = None
    completed_lessons: Optional[int] = None
    is_used: bool = False
    last_used: Optional[datetime] = None
    usage_count: int = 0

    class Config:
        from_attributes = True


class TemplateBase(BaseSchema):
    """Базовая схема шаблона"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
    structure: Dict[str, Any] = Field(..., description="The template structure")
    is_default: bool = False


class TemplateCreate(TemplateBase):
    """Схема для создания шаблона"""
    pass


class Template(TemplateBase):
    """Полная схема шаблона"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
