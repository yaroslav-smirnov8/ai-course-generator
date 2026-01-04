from fastapi import APIRouter, Depends
from typing import List

from .content import router as content_router
from .users import router as users_router
from .tracking import router as tracking_router
from .pricing import router as pricing_router
from .achievements import router as achievements_router
from .statistics import router as statistics_router
from .referral import router as referral_router
from .export import router as export_router
from .generations import router as generations_router
from .profile import router as profile_router
from .course import router as course_router
from .feature_usage import router as feature_usage_router
from .auth import router as auth_router
from .points import router as points_router
from .tariff import router as tariff_router  # For user-specific tariff routes
from .tariffs import router as tariffs_router  # For general tariff routes
from .app_usage import router as app_usage_router
from .link_clicks import router as link_clicks_router
from .advanced_analytics import router as advanced_analytics_router
from .analytics import router as analytics_router
from .promocodes import router as promocodes_router, user_router as promocodes_user_router
from .admin_users import router as admin_users_router
from .broadcast import router as broadcast_router
# from .endpoints.api_gateway import router as api_gateway_router  # Временно отключено для отладки
from ...core.security import get_current_user


# Проверка наличия обязательных роутеров
required_routers = {
    "auth": auth_router,
    "content": content_router,
    "users": users_router,
    "points": points_router,
    "tariff": tariff_router,
    "tariffs": tariffs_router
}

for name, router_instance in required_routers.items():
    if not router_instance:
        raise ImportError(f"Required router '{name}' is missing")

# Список всех роутеров
routers: List[tuple[APIRouter, str, List[str]]] = [
    (auth_router, "/auth", ["auth"]),
    (content_router, "/content", ["content"]),
    (users_router, "/users", ["users"]),
    (tracking_router, "/tracking", ["tracking"]),
    (pricing_router, "/pricing", ["pricing"]),
    (achievements_router, "", ["achievements"]),
    (statistics_router, "", ["statistics"]),
    (referral_router, "/referral", ["referral"]),
    (export_router, "/export", ["export"]),
    (generations_router, "", ["generations"]),
    (profile_router, "", ["profile"]),
    (course_router, "/course", ["course"]), # Возвращаем префикс /course
    (feature_usage_router, "", ["feature-usage"]),
    (points_router, "/points", ["points"]),
    (tariff_router, "/users", ["tariffs"]),  # User-specific tariff routes under /users
    (tariffs_router, "/tariffs", ["tariffs"]),  # General tariff routes under /tariffs
    (app_usage_router, "/analytics", ["analytics"]),
    (link_clicks_router, "/analytics", ["link-clicks"]),  # Роутер для переходов по ссылкам
    (advanced_analytics_router, "", ["advanced-analytics"]),  # Роутер для расширенной аналитики
    (analytics_router, "/admin/analytics", ["admin-analytics"]),  # Роутер для админской аналитики
    (promocodes_router, "", ["promocodes-admin"]),  # Админские промокоды
    (promocodes_user_router, "", ["promocodes-user"]),  # Пользовательские промокоды
    (admin_users_router, "", ["admin-users"]),  # Управление пользователями
    (broadcast_router, "/broadcast", ["broadcast"])  # Рассылка сообщений
    # (api_gateway_router, "/api-gateway", ["api-gateway"])  # Мониторинг API Gateway - временно отключено
]

router = APIRouter()

# Защищенные роутеры, требующие аутентификации
protected_routers = [
    content_router,
    profile_router,
    generations_router,
    course_router,
    feature_usage_router,
    points_router,
    tariff_router,
    tariffs_router,  # Don't forget to protect this router too
    app_usage_router,
    link_clicks_router,  # Защищаем роутер для переходов по ссылкам
    advanced_analytics_router,  # Защищаем роутер для расширенной аналитики
    analytics_router,  # Защищаем роутер для админской аналитики
    promocodes_router,  # Защищаем админские промокоды
    promocodes_user_router,  # Защищаем пользовательские промокоды
    admin_users_router,  # Защищаем управление пользователями
    broadcast_router  # Защищаем рассылку сообщений
    # api_gateway_router  # Защищаем мониторинг API Gateway - временно отключено
]

# Добавляем зависимость аутентификации
for router_instance in protected_routers:
    router_instance.dependencies = [Depends(get_current_user)]

# Подключаем все роутеры
for router_instance, prefix, tags in routers:
    router.include_router(
        router_instance,
        prefix=prefix,
        tags=tags
    )
