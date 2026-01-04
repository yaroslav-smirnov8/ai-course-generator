# app/api/v1/broadcast.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_admin_user
from ...models.user import User
from ...models.broadcast import ScheduledMessage
from ...schemas.user import UserInDB

router = APIRouter()


@router.get("/users/active", response_model=List[UserInDB])
async def get_active_users_for_broadcast(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Получить список активных пользователей для рассылки"""
    try:
        result = await db.execute(
            select(User)
            .where(User.notifications_enabled == True)
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )


@router.post("/send-to-user/{user_id}")
async def send_message_to_user(
    user_id: int,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Отправить персональное сообщение пользователю через бот"""
    try:
        # Проверяем, существует ли пользователь
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Создаем запись о персональном сообщении
        personal_message = ScheduledMessage(
            message_text=message,
            is_sent=False,
            created_by=current_admin.telegram_id,
            recipients_count=1,
            # Добавляем специальное поле для персональных сообщений
            message_photo_caption=f"personal_to_{user.telegram_id}"  # Используем это поле как флаг
        )
        
        db.add(personal_message)
        await db.commit()
        await db.refresh(personal_message)
        
        # Возвращаем URL для перехода в бот с параметрами
        bot_username = "neuro_teacher_bot"
        bot_url = f"https://t.me/{bot_username}?start=send_personal_{personal_message.id}_{user.telegram_id}"
        
        return {
            "success": True,
            "message_id": personal_message.id,
            "bot_url": bot_url,
            "user_telegram_id": user.telegram_id,
            "message": "Сообщение подготовлено. Перейдите в бот для отправки."
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.post("/broadcast")
async def create_broadcast(
    message: str,
    photo_url: Optional[str] = None,
    photo_caption: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Создать рассылку для всех пользователей"""
    try:
        # Создаем запись о рассылке
        broadcast_message = ScheduledMessage(
            message_text=message,
            message_photo_path=photo_url,
            message_photo_caption=photo_caption,
            scheduled_time=scheduled_time,
            is_sent=False,
            created_by=current_admin.telegram_id
        )
        
        db.add(broadcast_message)
        await db.commit()
        await db.refresh(broadcast_message)
        
        # Возвращаем URL для перехода в бот
        bot_username = "neuro_teacher_bot"
        if scheduled_time:
            bot_url = f"https://t.me/{bot_username}?start=schedule_broadcast_{broadcast_message.id}"
        else:
            bot_url = f"https://t.me/{bot_username}?start=send_broadcast_{broadcast_message.id}"
        
        return {
            "success": True,
            "message_id": broadcast_message.id,
            "bot_url": bot_url,
            "message": "Рассылка подготовлена. Перейдите в бот для отправки."
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating broadcast: {str(e)}"
        )


@router.get("/statistics")
async def get_broadcast_statistics(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Получить статистику рассылок"""
    try:
        # Получаем все сообщения админа
        result = await db.execute(
            select(ScheduledMessage).where(ScheduledMessage.created_by == current_admin.telegram_id)
        )
        messages = result.scalars().all()

        total_messages = len(messages)
        sent_messages = len([m for m in messages if m.is_sent])
        pending_messages = total_messages - sent_messages
        
        total_recipients = sum(m.recipients_count or 0 for m in messages if m.is_sent)
        total_success = sum(m.success_count or 0 for m in messages if m.is_sent)
        total_errors = sum(m.error_count or 0 for m in messages if m.is_sent)

        return {
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "pending_messages": pending_messages,
            "total_recipients": total_recipients,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": round((total_success / total_recipients * 100) if total_recipients > 0 else 0, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}"
        )


@router.get("/history")
async def get_broadcast_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Получить историю рассылок"""
    try:
        result = await db.execute(
            select(ScheduledMessage)
            .where(ScheduledMessage.created_by == current_admin.telegram_id)
            .order_by(ScheduledMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        messages = result.scalars().all()
        
        return [
            {
                "id": msg.id,
                "message_text": msg.message_text,
                "message_photo_caption": msg.message_photo_caption,
                "is_sent": msg.is_sent,
                "created_at": msg.created_at,
                "sent_at": msg.sent_at,
                "recipients_count": msg.recipients_count,
                "success_count": msg.success_count,
                "error_count": msg.error_count,
                "is_personal": msg.message_photo_caption and msg.message_photo_caption.startswith("personal_to_")
            }
            for msg in messages
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting history: {str(e)}"
        )
