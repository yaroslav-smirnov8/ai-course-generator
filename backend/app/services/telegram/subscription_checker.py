"""
Сервис для проверки подписки пользователей на обязательные каналы
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SubscriptionChecker:
    """Сервис для проверки подписки на Telegram каналы"""

    def __init__(self):
        self.settings = get_settings()
        self.bot_token = self.settings.BOT_TOKEN
        self.required_channel_id = self.settings.REQUIRED_CHANNEL_ID
        self.required_channel_url = self.settings.REQUIRED_CHANNEL_URL
        self.evo_channel_id = self.settings.EVO_CHANNEL_ID
        self.evo_channel_url = self.settings.EVO_CHANNEL_URL

    async def check_channel_subscription(self, user_id: int) -> Dict[str, Any]:
        """
        Проверяет подписку пользователя на обязательный канал

        Args:
            user_id: Telegram ID пользователя

        Returns:
            Dict с результатом проверки:
            {
                "is_subscribed": bool,
                "channel_url": str,
                "error": Optional[str]
            }
        """
        if not self.required_channel_id:
            # Если канал не настроен, считаем что подписка не требуется
            return {
                "is_subscribed": True,
                "channel_url": None,
                "error": None
            }

        try:
            # Проверяем подписку через Telegram Bot API
            url = f"https://api.telegram.org/bot{self.bot_token}/getChatMember"
            params = {
                "chat_id": self.required_channel_id,
                "user_id": user_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("ok"):
                            member_status = data.get("result", {}).get("status")

                            # Статусы, которые считаются подпиской
                            subscribed_statuses = ["member", "administrator", "creator"]
                            is_subscribed = member_status in subscribed_statuses

                            logger.info(f"User {user_id} subscription status: {member_status}")

                            return {
                                "is_subscribed": is_subscribed,
                                "channel_url": self.required_channel_url,
                                "error": None
                            }
                        else:
                            error_msg = data.get("description", "Unknown API error")
                            logger.warning(f"Telegram API error for user {user_id}: {error_msg}")

                            # Если пользователь не найден в канале, считаем что не подписан
                            if "user not found" in error_msg.lower() or "chat not found" in error_msg.lower():
                                return {
                                    "is_subscribed": False,
                                    "channel_url": self.required_channel_url,
                                    "error": None
                                }

                            return {
                                "is_subscribed": False,
                                "channel_url": self.required_channel_url,
                                "error": error_msg
                            }
                    else:
                        logger.error(f"HTTP error {response.status} when checking subscription for user {user_id}")
                        return {
                            "is_subscribed": False,
                            "channel_url": self.required_channel_url,
                            "error": f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            logger.error(f"Timeout when checking subscription for user {user_id}")
            return {
                "is_subscribed": False,
                "channel_url": self.required_channel_url,
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id}: {str(e)}")
            return {
                "is_subscribed": False,
                "channel_url": self.required_channel_url,
                "error": str(e)
            }

    async def check_evo_channel_subscription(self, user_id: int) -> Dict[str, Any]:
        """
        Проверяет подписку пользователя на канал приложения (EVO_CHANNEL_ID)

        Args:
            user_id: Telegram ID пользователя

        Returns:
            Dict с результатом проверки:
            {
                "is_subscribed": bool,
                "channel_url": str,
                "error": Optional[str]
            }
        """
        if not self.evo_channel_id:
            # Если канал приложения не настроен, возвращаем ошибку конфигурации
            return {
                "is_subscribed": False,
                "channel_url": None,
                "error": "EVO channel not configured"
            }

        try:
            # Проверяем подписку через Telegram Bot API
            url = f"https://api.telegram.org/bot{self.bot_token}/getChatMember"
            params = {
                "chat_id": self.evo_channel_id,
                "user_id": user_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("ok"):
                            member_status = data.get("result", {}).get("status")

                            # Статусы, которые считаются подпиской
                            subscribed_statuses = ["member", "administrator", "creator"]
                            is_subscribed = member_status in subscribed_statuses

                            logger.info(f"User {user_id} EVO channel subscription status: {member_status}")

                            return {
                                "is_subscribed": is_subscribed,
                                "channel_url": self.evo_channel_url,
                                "error": None
                            }
                        else:
                            error_msg = data.get("description", "Unknown API error")
                            logger.warning(f"Telegram API error for user {user_id} (EVO channel): {error_msg}")

                            # Если пользователь не найден в канале, считаем что не подписан
                            if "user not found" in error_msg.lower() or "chat not found" in error_msg.lower():
                                return {
                                    "is_subscribed": False,
                                    "channel_url": self.evo_channel_url,
                                    "error": None
                                }

                            return {
                                "is_subscribed": False,
                                "channel_url": self.evo_channel_url,
                                "error": error_msg
                            }
                    else:
                        logger.error(f"HTTP error {response.status} when checking EVO channel subscription for user {user_id}")
                        return {
                            "is_subscribed": False,
                            "channel_url": self.evo_channel_url,
                            "error": f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            logger.error(f"Timeout when checking EVO channel subscription for user {user_id}")
            return {
                "is_subscribed": False,
                "channel_url": self.evo_channel_url,
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Error checking EVO channel subscription for user {user_id}: {str(e)}")
            return {
                "is_subscribed": False,
                "channel_url": self.evo_channel_url,
                "error": str(e)
            }

    async def check_user_access(self, user_id: int, has_access: bool) -> Dict[str, Any]:
        """
        Комплексная проверка доступа пользователя (бан + подписка на оба обязательных канала)

        Args:
            user_id: Telegram ID пользователя
            has_access: Статус доступа из базы данных

        Returns:
            Dict с результатом проверки:
            {
                "access_granted": bool,
                "reason": str,  # "banned", "not_subscribed", "evo_not_subscribed", "ok"
                "channel_url": Optional[str],
                "error": Optional[str]
            }
        """
        # Сначала проверяем бан
        if not has_access:
            logger.info(f"User {user_id} is banned")
            return {
                "access_granted": False,
                "reason": "banned",
                "channel_url": None,
                "error": None
            }

        # Затем проверяем подписку на основной канал
        subscription_result = await self.check_channel_subscription(user_id)

        if not subscription_result["is_subscribed"]:
            logger.info(f"User {user_id} is not subscribed to required channel")
            return {
                "access_granted": False,
                "reason": "not_subscribed",
                "channel_url": subscription_result["channel_url"],
                "error": subscription_result["error"]
            }

        # Проверяем подписку на канал EVO (обязательно, если настроен)
        if self.evo_channel_id:  # Проверяем только если канал настроен
            evo_subscription_result = await self.check_evo_channel_subscription(user_id)

            if not evo_subscription_result["is_subscribed"]:
                logger.info(f"User {user_id} is not subscribed to EVO channel (required for access)")
                return {
                    "access_granted": False,
                    "reason": "evo_not_subscribed",
                    "channel_url": evo_subscription_result["channel_url"],
                    "error": evo_subscription_result["error"]
                }

        # Все проверки пройдены
        return {
            "access_granted": True,
            "reason": "ok",
            "channel_url": None,
            "error": None
        }


# Глобальный экземпляр для использования в приложении
subscription_checker = SubscriptionChecker()
