# app/services/points/utils.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from ...schemas.points import TransactionType
from ...core.constants import ContentType


def calculate_generation_cost(
        content_type: ContentType,
        user_tariff: str,
        tariff_settings: Dict[str, Any]
) -> int:
    """
    Вычисляет стоимость генерации в зависимости от типа контента и тарифа
    """
    # Базовая стоимость для разных типов контента
    base_costs = {
        ContentType.LESSON_PLAN: 10,
        ContentType.COURSE_LESSON_PLAN: 10,  # Та же стоимость что и обычные планы
        ContentType.EXERCISE: 5,
        ContentType.COURSE_EXERCISE: 5,      # Та же стоимость что и обычные упражнения
        ContentType.GAME: 5,
        ContentType.COURSE_GAME: 5,          # Та же стоимость что и обычные игры
        ContentType.IMAGE: 15,
        ContentType.TRANSCRIPT: 8
    }

    # Получаем базовую стоимость
    base_cost = base_costs.get(content_type, 10)

    # Получаем множитель скидки для тарифа
    tariff_discounts = {
        'tariff_2': 1.0,  # Базовый тариф - без скидки
        'tariff_4': 0.9,  # Стандартный тариф - скидка 10%
        'tariff_6': 0.8  # Премиум тариф - скидка 20%
    }

    discount_multiplier = tariff_discounts.get(user_tariff, 1.0)

    # Применяем настройки тарифа, если они есть
    if tariff_settings and user_tariff in tariff_settings:
        custom_cost = tariff_settings[user_tariff].get(f"{content_type.value}_cost")
        if custom_cost is not None:
            base_cost = custom_cost

    # Вычисляем финальную стоимость
    return int(base_cost * discount_multiplier)


def format_transaction_description(
        transaction_type: TransactionType,
        content_type: Optional[ContentType] = None,
        meta_data: Optional[Dict] = None
) -> str:
    """
    Форматирует описание транзакции
    """
    descriptions = {
        TransactionType.GENERATION: f"Generation of {content_type.value if content_type else 'content'}",
        TransactionType.PURCHASE: "Points purchase",
        TransactionType.REWARD: "Reward points",
        TransactionType.REFUND: "Points refund",
        TransactionType.INVITE_BONUS: "Invitation bonus",
        TransactionType.ACHIEVEMENT: "Achievement reward",
        TransactionType.ADMIN_CORRECTION: "Administrative correction"
    }

    base_description = descriptions.get(transaction_type, "Point transaction")

    if meta_data:
        additional_info = []
        if meta_data.get("achievement_name"):
            additional_info.append(f"Achievement: {meta_data['achievement_name']}")
        if meta_data.get("invite_code"):
            additional_info.append(f"Invite code: {meta_data['invite_code']}")
        if meta_data.get("refund_reason"):
            additional_info.append(f"Reason: {meta_data['refund_reason']}")

        if additional_info:
            base_description += f" ({', '.join(additional_info)})"

    return base_description


def calculate_daily_limits(
        user_tariff: str,
        tariff_settings: Dict[str, Any]
) -> Dict[str, int]:
    """
    Вычисляет дневные лимиты генераций для тарифа
    """
    default_limits = {
        'tariff_2': {  # Базовый тариф
            'generations': 10,
            'images': 5
        },
        'tariff_4': {  # Стандартный тариф
            'generations': 20,
            'images': 10
        },
        'tariff_6': {  # Премиум тариф
            'generations': 30,
            'images': 15
        }
    }

    # Берем базовые лимиты для тарифа
    limits = default_limits.get(user_tariff, default_limits['tariff_2']).copy()

    # Применяем кастомные настройки, если они есть
    if tariff_settings and user_tariff in tariff_settings:
        custom_settings = tariff_settings[user_tariff]
        if 'generations_limit' in custom_settings:
            limits['generations'] = custom_settings['generations_limit']
        if 'images_limit' in custom_settings:
            limits['images'] = custom_settings['images_limit']

    return limits


def check_transaction_time_limit(
        last_transaction_time: Optional[datetime],
        transaction_type: TransactionType,
        current_time: Optional[datetime] = None
) -> bool:
    """
    Проверяет временные ограничения для транзакций
    """
    if not current_time:
        current_time = datetime.now(timezone.utc)

    if not last_transaction_time:
        return True

    # Минимальные интервалы между транзакциями разных типов
    time_limits = {
        TransactionType.GENERATION: timedelta(seconds=5),  # 5 секунд между генерациями
        TransactionType.PURCHASE: timedelta(minutes=1),  # 1 минута между покупками
        TransactionType.REWARD: timedelta(minutes=5),  # 5 минут между наградами
        TransactionType.INVITE_BONUS: timedelta(hours=1),  # 1 час между бонусами за приглашения
    }

    minimum_interval = time_limits.get(transaction_type, timedelta(0))
    return current_time - last_transaction_time >= minimum_interval


def validate_transaction_amount(
        amount: int,
        transaction_type: TransactionType
) -> bool:
    """
    Проверяет валидность суммы транзакции
    """
    # Минимальные и максимальные значения для разных типов транзакций
    limits = {
        TransactionType.GENERATION: {
            'min': 1,
            'max': 100
        },
        TransactionType.PURCHASE: {
            'min': 100,
            'max': 10000
        },
        TransactionType.REWARD: {
            'min': 5,
            'max': 1000
        },
        TransactionType.INVITE_BONUS: {
            'min': 10,
            'max': 500
        },
        TransactionType.ACHIEVEMENT: {
            'min': 5,
            'max': 1000
        }
    }

    type_limits = limits.get(transaction_type, {'min': 1, 'max': 10000})
    return type_limits['min'] <= amount <= type_limits['max']