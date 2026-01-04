# app/services/queue/base.py
from datetime import datetime
from typing import Optional, Any
from ...schemas.content import GenerationStatus


class QueueItem:
    """Base class representing an item in the processing queue"""

    def __init__(
            self,
            task_id: int,
            user_id: int,
            content_type: str,
            prompt: str,
            priority: int = 0
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.content_type = content_type
        self.prompt = prompt
        self.priority = priority
        self.status = GenerationStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None

    def __lt__(self, other):
        # For priority queue comparison
        return self.priority > other.priority