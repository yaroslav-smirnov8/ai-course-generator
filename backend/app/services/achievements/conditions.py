from typing import Dict, Any
from enum import Enum

class AchievementType(Enum):
    GENERATION = "generation"
    IMAGE = "image"
    STREAK = "streak"
    INVITE = "invite"
    POINTS = "points"

class AchievementConditions:
    @staticmethod
    def get_generation_conditions(count: int, content_type: str = None) -> Dict[str, Any]:
        """Создает условия для достижений по генерациям"""
        return {
            "type": AchievementType.GENERATION.value,
            "generation_count": count,
            "content_type": content_type
        }

    @staticmethod
    def get_image_conditions(count: int) -> Dict[str, Any]:
        """Создает условия для достижений по изображениям"""
        return {
            "type": AchievementType.IMAGE.value,
            "image_count": count
        }

    @staticmethod
    def get_streak_conditions(days: int) -> Dict[str, Any]:
        """Создает условия для достижений по последовательным дням"""
        return {
            "type": AchievementType.STREAK.value,
            "consecutive_days": days
        }

    @staticmethod
    def get_invite_conditions(count: int) -> Dict[str, Any]:
        """Создает условия для достижений по приглашениям"""
        return {
            "type": AchievementType.INVITE.value,
            "invites_count": count
        }

    @staticmethod
    def get_points_conditions(points: int) -> Dict[str, Any]:
        """Создает условия для достижений по баллам"""
        return {
            "type": AchievementType.POINTS.value,
            "points_required": points
        }

    # Предопределенные достижения
    ACHIEVEMENTS = {
        "first_generation": {
            "code": "FIRST_GEN",
            "name": "First Generation",
            "description": "Create your first content",
            "conditions": get_generation_conditions(1),
            "points_reward": 10
        },
        "generation_master": {
            "code": "GEN_MASTER",
            "name": "Generation Master",
            "description": "Create 100 content items",
            "conditions": get_generation_conditions(100),
            "points_reward": 100
        },
        "image_creator": {
            "code": "IMG_CREATOR",
            "name": "Image Creator",
            "description": "Create 50 images",
            "conditions": get_image_conditions(50),
            "points_reward": 50
        },
        "daily_streak": {
            "code": "DAILY_7",
            "name": "Weekly Streak",
            "description": "Use the app for 7 consecutive days",
            "conditions": get_streak_conditions(7),
            "points_reward": 70
        },
        "inviter": {
            "code": "INVITE_5",
            "name": "Inviter",
            "description": "Invite 5 friends",
            "conditions": get_invite_conditions(5),
            "points_reward": 100
        }
    }