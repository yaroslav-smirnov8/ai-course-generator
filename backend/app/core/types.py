# app/core/types.py
from enum import Enum

class ContentType(str, Enum):
    LESSON_PLAN = "lesson_plan"
    EXERCISE = "exercise"
    GAME = "game"
    IMAGE = "image"
    TRANSCRIPT = "transcript"
    TEXT_ANALYSIS = "text_analysis"
    CONCEPT_EXPLANATION = "concept_explanation"
    FREE_QUERY = "free_query"
    COURSE = "course"
    STRUCTURED_DATA = "structured_data"
    LESSON_MATERIAL = "lesson_material"
    COURSE_EXPORT = "course_export"

class TariffType(str, Enum):
    BASIC = "tariff_2"
    STANDARD = "tariff_4"
    PREMIUM = "tariff_6"

# Добавляем ActionType для совместимости
class ActionType(str, Enum):
    GENERATION = "generation"
    VIEW = "view"
    EDIT = "edit"
    SHARE = "share"
    DOWNLOAD = "download"
    DELETE = "delete"