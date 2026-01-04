# schemas/generations.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.constants import ContentType
from .base import BaseSchema

class GenerationBase(BaseSchema):
    type: ContentType
    content: str
    prompt: str

class GenerationCreate(GenerationBase):
    user_id: int

class GenerationResponse(GenerationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GenerationListResponse(BaseSchema):
    items: List[GenerationResponse]
    total: int

class GenerationFilter(BaseSchema):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    type: Optional[ContentType] = None
    user_id: Optional[int] = None