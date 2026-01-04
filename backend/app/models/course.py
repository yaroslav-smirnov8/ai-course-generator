from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, JSON, Enum, Boolean, Text, DateTime # Добавлен Text
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from ..core.database import Base
from ..core.constants import CourseLevel, CourseFormat, TargetAudience

class Course(AsyncAttrs, Base):
    __tablename__ = "courses"

    # Основные поля
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[CourseLevel] = mapped_column(Enum(CourseLevel), nullable=False)
    start_level: Mapped[Optional[CourseLevel]] = mapped_column(Enum(CourseLevel), nullable=True)
    target_audience: Mapped[TargetAudience] = mapped_column(Enum(TargetAudience), nullable=False)
    format: Mapped[CourseFormat] = mapped_column(Enum(CourseFormat), nullable=False)
    total_duration: Mapped[int] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exam_prep: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prerequisites: Mapped[List] = mapped_column(JSON, default=list)
    learning_outcomes: Mapped[List] = mapped_column(JSON, default=list)

    # Дополнительная информация о курсе
    methodology: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    student_age: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    student_interests: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    student_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_mistakes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_exam: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    exam_prep_lessons: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Настройки генерации курса
    lessons_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    lesson_duration: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    grammar_focus: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vocabulary_focus: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Настройки типов контента
    include_speaking: Mapped[bool] = mapped_column(Boolean, default=True)
    include_listening: Mapped[bool] = mapped_column(Boolean, default=True)
    include_reading: Mapped[bool] = mapped_column(Boolean, default=True)
    include_writing: Mapped[bool] = mapped_column(Boolean, default=True)
    include_games: Mapped[bool] = mapped_column(Boolean, default=True)

    # Поля для отслеживания использования
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    usage_count: Mapped[int] = mapped_column(default=0)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Отношения
    lessons: Mapped[List["Lesson"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    creator: Mapped["User"] = relationship(
        back_populates="courses",
        lazy="selectin"
    )

class Lesson(AsyncAttrs, Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    order: Mapped[int] = mapped_column(nullable=False)
    objectives: Mapped[List] = mapped_column(JSON, default=list)
    grammar: Mapped[List] = mapped_column(JSON, default=list)
    vocabulary: Mapped[List] = mapped_column(JSON, default=list)
    materials: Mapped[List] = mapped_column(JSON, default=list)
    homework: Mapped[Dict] = mapped_column(JSON, default=dict)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # <-- НОВОЕ ПОЛЕ
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Отношения
    course: Mapped["Course"] = relationship(
        back_populates="lessons",
        lazy="selectin"
    )
    activities: Mapped[List["Activity"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class Activity(AsyncAttrs, Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    materials: Mapped[List] = mapped_column(JSON, default=list)
    objectives: Mapped[List] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Отношения
    lesson: Mapped["Lesson"] = relationship(
        back_populates="activities",
        lazy="selectin"
    )

class LessonTemplate(AsyncAttrs, Base):
    __tablename__ = "lesson_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    structure: Mapped[Dict] = mapped_column(JSON, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
