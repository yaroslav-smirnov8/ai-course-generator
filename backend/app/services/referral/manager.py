from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text, exists
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import uuid
import logging
from ...models import User, UserAction, PointTransaction, Generation
from ...core.constants import ActionType
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
from ...core.cache import CacheService

logger = logging.getLogger(__name__)


class ReferralManager:
    def __init__(self, session: AsyncSession, cache: CacheService):
        self.session = session
        self.cache = cache
        self.batch_processor = BatchProcessor(session)
        self.query_optimizer = QueryOptimizer(session)
        self.invite_points_reward = 100  # Настраиваемая награда за приглашение
        self.max_chain_depth = 3  # Максимальная глубина цепочки рефералов
        self.cache_ttl = 3600  # Время жизни кэша в секундах

    async def get_invite_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает оптимизированную статистику приглашений пользователя"""
        try:
            # Проверяем кэш
            cache_key = f"invite_stats:{user_id}"
            cached_stats = await self.cache.get_cached_data(cache_key)
            if cached_stats:
                return cached_stats

            # Получаем базовую информацию о пользователе через оптимизатор
            user_query = await self.query_optimizer.optimize_query(
                select(User).where(User.id == user_id)
            )
            result = await self.session.execute(user_query)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Получаем количество активных приглашений через оптимизатор
            active_invites_query = await self.query_optimizer.optimize_query(
                select(func.count(User.id)).where(
                    and_(
                        User.invited_by_code == user.invite_code,
                        User.has_access == True
                    )
                )
            )
            result = await self.session.execute(active_invites_query)
            active_invites = result.scalar_one()

            # Собираем статистику
            stats = {
                "invite_code": user.invite_code,
                "total_invites": user.invites_count,
                "active_invites": active_invites,
                "total_points_earned": await self._calculate_referral_points(user_id),
                "effective_discount": user.effective_discount,
                "can_invite": await self._check_invite_availability(user_id)
            }

            # Кэшируем результат
            await self.cache.cache_data(cache_key, stats, ttl=self.cache_ttl)
            return stats

        except Exception as e:
            logger.error(f"Error getting invite stats: {str(e)}")
            raise

    async def process_invite(self, invite_code: str, new_user_id: int) -> bool:
        """Оптимизированная обработка использования пригласительного кода"""
        try:
            # Получаем пригласившего пользователя через оптимизатор
            inviter_query = await self.query_optimizer.optimize_query(
                select(User).where(User.invite_code == invite_code)
            )
            result = await self.session.execute(inviter_query)
            inviter = result.scalar_one_or_none()

            # Получаем нового пользователя через оптимизатор
            new_user_query = await self.query_optimizer.optimize_query(
                select(User).where(User.id == new_user_id)
            )
            result = await self.session.execute(new_user_query)
            new_user = result.scalar_one_or_none()

            if not inviter or not new_user or new_user.invited_by_code:
                return False

            # Подготавливаем batch-операции
            batch_operations = []

            # Обновление нового пользователя
            new_user.invited_by_code = invite_code
            new_user.effective_discount = 1  # 1% скидка новому пользователю
            batch_operations.append(new_user)

            # Обновление пригласившего
            inviter.invites_count += 1
            inviter.effective_discount = min(
                inviter.effective_discount + 2,  # +2% пригласившему
                20  # Максимальная скидка 20%
            )
            batch_operations.append(inviter)

            # Создаем записи о наградах
            invite_action = UserAction(
                user_id=inviter.id,
                action_type=ActionType.INVITE_USED,
                content_type=None,
                activity_metadata={
                    "invited_user_id": new_user_id,
                    "invite_code": invite_code
                }
            )
            batch_operations.append(invite_action)

            # Начисляем баллы
            points_transaction = PointTransaction(
                user_id=inviter.id,
                amount=self.invite_points_reward,
                transaction_type="invite_reward",
                description=f"Reward for inviting user {new_user_id}"
            )
            batch_operations.append(points_transaction)

            # Выполняем batch-операции
            await self.batch_processor.bulk_insert(batch_operations)

            # Инвалидируем кэш
            await self.cache.invalidate_pattern(f"invite_stats:{inviter.id}*")
            await self.cache.invalidate_pattern(f"referral_chain:{inviter.id}*")

            return True

        except Exception as e:
            logger.error(f"Error processing invite: {str(e)}")
            await self.session.rollback()
            raise

    async def get_referral_chain(self, user_id: int, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Получает оптимизированную цепочку рефералов"""
        try:
            depth = max_depth or self.max_chain_depth
            cache_key = f"referral_chain:{user_id}:{depth}"

            # Проверяем кэш
            cached_chain = await self.cache.get_cached_data(cache_key)
            if cached_chain:
                return cached_chain

            # Оптимизированный рекурсивный запрос через CTE
            with_recursive = """
                WITH RECURSIVE referral_chain AS (
                    -- Базовый случай
                    SELECT 
                        u.id,
                        u.invite_code,
                        u.invited_by_code,
                        u.invites_count,
                        1 as level
                    FROM users u
                    WHERE u.id = :user_id

                    UNION ALL

                    -- Рекурсивная часть
                    SELECT
                        u.id,
                        u.invite_code,
                        u.invited_by_code,
                        u.invites_count,
                        rc.level + 1
                    FROM users u
                    INNER JOIN referral_chain rc ON u.invite_code = rc.invited_by_code
                    WHERE rc.level < :max_depth
                )
                SELECT 
                    id,
                    invite_code,
                    invited_by_code,
                    invites_count,
                    level
                FROM referral_chain
                ORDER BY level, id
            """

            # Выполняем оптимизированный запрос
            result = await self.session.execute(
                text(with_recursive),
                {"user_id": user_id, "max_depth": depth}
            )
            chain_data = result.fetchall()

            # Обрабатываем результаты
            chain = []
            total_invites = 0
            levels = {}

            for row in chain_data:
                user_data = {
                    "user_id": row.id,
                    "invites_count": row.invites_count,
                    "level": row.level
                }
                chain.append(user_data)
                total_invites += row.invites_count

                if row.level not in levels:
                    levels[row.level] = 0
                levels[row.level] += 1

            result = {
                "chain": chain,
                "total_invites": total_invites,
                "total_users": len(chain),
                "max_depth": depth,
                "levels_distribution": levels
            }

            # Кэшируем результат
            await self.cache.cache_data(cache_key, result, ttl=self.cache_ttl)
            return result

        except Exception as e:
            logger.error(f"Error getting referral chain: {str(e)}")
            raise

    async def generate_invite_code(self) -> str:
        """Генерирует уникальный пригласительный код"""
        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            code = str(uuid.uuid4())[:8]

            # Проверяем уникальность через оптимизатор
            exists_query = await self.query_optimizer.optimize_query(
                select(exists().where(User.invite_code == code))
            )
            result = await self.session.execute(exists_query)

            if not result.scalar_one():
                return code

            attempt += 1

        raise Exception("Failed to generate unique invite code")

    async def get_user_invites(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список приглашенных пользователей"""
        try:
            cache_key = f"user_invites:{user_id}"
            cached_invites = await self.cache.get_cached_data(cache_key)
            if cached_invites:
                return cached_invites

            # Оптимизированный запрос через batch processor
            query = await self.query_optimizer.optimize_query(
                select(User).where(
                    User.invited_by_code.in_(
                        select(User.invite_code).where(User.id == user_id)
                    )
                )
            )

            invited_users = []
            async for chunk in self.batch_processor.process_query_in_chunks(query):
                for user in chunk:
                    invited_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "joined_at": user.created_at.isoformat(),
                        "is_active": user.has_access,
                        "total_generations": await self._get_user_generations_count(user.id)
                    })

            # Кэшируем результат
            await self.cache.cache_data(cache_key, invited_users, ttl=self.cache_ttl)
            return invited_users

        except Exception as e:
            logger.error(f"Error getting user invites: {str(e)}")
            raise

    async def _calculate_referral_points(self, user_id: int) -> int:
        """Подсчитывает заработанные реферальные баллы"""
        try:
            query = await self.query_optimizer.optimize_query(
                select(func.sum(PointTransaction.amount)).where(
                    and_(
                        PointTransaction.user_id == user_id,
                        PointTransaction.transaction_type == "invite_reward"
                    )
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one() or 0

        except Exception as e:
            logger.error(f"Error calculating referral points: {str(e)}")
            return 0

    async def _check_invite_availability(self, user_id: int) -> bool:
        """Проверяет возможность приглашать новых пользователей"""
        try:
            # Проверяем ограничения на приглашения
            user_query = await self.query_optimizer.optimize_query(
                select(User).where(User.id == user_id)
            )
            result = await self.session.execute(user_query)
            user = result.scalar_one_or_none()

            if not user:
                return False

            # Проверяем активность пользователя
            return (
                    user.has_access and
                    (datetime.utcnow() - user.created_at).days >= 7 and  # Минимальный возраст аккаунта
                    user.invites_count < 100  # Максимальное количество приглашений
            )

        except Exception as e:
            logger.error(f"Error checking invite availability: {str(e)}")
            return False

    async def _get_user_generations_count(self, user_id: int) -> int:
        """Получает количество генераций пользователя"""
        try:
            cache_key = f"user_generations_count:{user_id}"
            cached_count = await self.cache.get_cached_data(cache_key)
            if cached_count is not None:
                return cached_count

            query = await self.query_optimizer.optimize_query(
                select(func.count(Generation.id)).where(Generation.user_id == user_id)
            )
            result = await self.session.execute(query)
            count = result.scalar_one() or 0

            # Кэшируем результат на короткое время
            await self.cache.cache_data(cache_key, count, ttl=300)  # 5 минут
            return count

        except Exception as e:
            logger.error(f"Error getting user generations count: {str(e)}")
            return 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()