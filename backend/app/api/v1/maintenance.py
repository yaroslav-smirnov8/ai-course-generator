"""
API для управления задачами обслуживания системы.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import get_current_user, get_current_admin_user
from ...services.maintenance.daily_cleanup import DailyMaintenanceService

router = APIRouter()

@router.post("/admin/maintenance/run", summary="Запустить все задачи обслуживания")
async def run_all_maintenance(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)  # Только для администраторов
):
    """
    Запускает все задачи обслуживания системы в фоновом режиме.
    
    Returns:
        dict: Информация о запуске задач
    """
    # Создаем функцию для выполнения в фоне
    async def run_tasks():
        async with DailyMaintenanceService(db) as service:
            await service.run_all_maintenance_tasks()
    
    # Добавляем задачу в фоновые
    background_tasks.add_task(run_tasks)
    
    return {
        "success": True,
        "message": "Задачи обслуживания запущены в фоновом режиме"
    }

@router.post("/admin/maintenance/reset-usage", summary="Сбросить счетчики дневного использования")
async def reset_daily_usage(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)  # Только для администраторов
):
    """
    Сбрасывает счетчики дневного использования для всех пользователей.
    
    Returns:
        dict: Информация о запуске задачи
    """
    # Создаем функцию для выполнения в фоне
    async def run_task():
        async with DailyMaintenanceService(db) as service:
            await service.reset_daily_usage()
    
    # Добавляем задачу в фоновые
    background_tasks.add_task(run_task)
    
    return {
        "success": True,
        "message": "Задача сброса счетчиков запущена в фоновом режиме"
    }

@router.post("/admin/maintenance/cleanup-logs", summary="Очистить старые логи использования")
async def cleanup_usage_logs(
    background_tasks: BackgroundTasks,
    days_to_keep: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)  # Только для администраторов
):
    """
    Удаляет старые записи из логов использования.
    
    Args:
        days_to_keep: Количество дней, за которые нужно сохранить логи
        
    Returns:
        dict: Информация о запуске задачи
    """
    # Создаем функцию для выполнения в фоне
    async def run_task():
        async with DailyMaintenanceService(db) as service:
            await service.cleanup_usage_logs(days_to_keep)
    
    # Добавляем задачу в фоновые
    background_tasks.add_task(run_task)
    
    return {
        "success": True,
        "message": f"Задача очистки логов старше {days_to_keep} дней запущена в фоновом режиме"
    }

@router.post("/admin/maintenance/check-expired-tariffs", summary="Проверить истекшие тарифы")
async def check_expired_tariffs(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)  # Только для администраторов
):
    """
    Проверяет истекшие тарифы и обновляет статус пользователей.
    
    Returns:
        dict: Информация о запуске задачи
    """
    # Создаем функцию для выполнения в фоне
    async def run_task():
        async with DailyMaintenanceService(db) as service:
            await service.check_expired_tariffs()
    
    # Добавляем задачу в фоновые
    background_tasks.add_task(run_task)
    
    return {
        "success": True,
        "message": "Задача проверки истекших тарифов запущена в фоновом режиме"
    } 