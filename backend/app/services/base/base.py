# app/services/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from ...repositories.base import BaseRepository
from typing import TypeVar, Type, Generic, Optional, List, Any

ModelType = TypeVar("ModelType")
RepoType = TypeVar("RepoType", bound=BaseRepository)

class BaseService(Generic[ModelType, RepoType]):
    def __init__(self, session: AsyncSession, repository_class: Type[RepoType]):
        self.session = session
        self.repository = repository_class(session)

    async def get(self, id: Any) -> Optional[ModelType]:
        return await self.repository.get(id)

    async def get_many(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create(self, data: dict) -> ModelType:
        return await self.repository.create(data)

    async def update(self, id: Any, data: dict) -> Optional[ModelType]:
        return await self.repository.update(id, data)

    async def delete(self, id: Any) -> bool:
        return await self.repository.delete(id)

    async def exists(self, id: Any) -> bool:
        return await self.repository.exists(id)