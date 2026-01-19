"""Сервис для отправки уведомлений пользователям и партнерам."""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from database.models import User, Partner, CycleEntry, Notification
from services.cycle_service import CycleService, PhaseInfo
from services.phase_formatter import PhaseFormatter
from services.partner_service import PartnerService

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений о фазах цикла."""
    
    NOTIFICATION_TYPE_PHASE_CHANGE = "phase_change"
    NOTIFICATION_TYPE_WEEKLY_REMINDER = "weekly_reminder"
    NOTIFICATION_TYPE_PARTNER_PHASE_CHANGE = "partner_phase_change"
    
    @staticmethod
    async def send_phase_change_notification(
        bot: Bot,
        db_session: AsyncSession,
        user: User,
        phase_info: PhaseInfo
    ) -> bool:
        """
        Отправляет уведомление пользователю о переходе в новую фазу.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
            db_session: Сессия базы данных
            user: Пользователь, которому отправляется уведомление
            phase_info: Информация о новой фазе цикла
            
        Returns:
            True, если уведомление отправлено успешно
        """
        if not user.notification_enabled:
            return False
        
        try:
            # Форматируем полную информацию о фазе
            phase_text = PhaseFormatter.format_phase_info(
                phase_info,
                include_partner_advice=False
            )
            
            message_text = (
                f"🔄 *Переход в новую фазу!*\n\n"
                f"{phase_text}"
            )
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                parse_mode="Markdown"
            )
            
            # Сохраняем запись об уведомлении
            notification = Notification(
                user_id=user.id,
                notification_type=NotificationService.NOTIFICATION_TYPE_PHASE_CHANGE,
                sent_at=datetime.now()
            )
            db_session.add(notification)
            await db_session.flush()
            
            logger.info(f"Отправлено уведомление о смене фазы пользователю {user.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user.telegram_id}: {e}")
            return False
    
    @staticmethod
    async def send_partner_phase_change_notification(
        bot: Bot,
        db_session: AsyncSession,
        partner: Partner,
        user: User,
        phase_info: PhaseInfo
    ) -> bool:
        """
        Отправляет уведомление партнеру о переходе пользователя в новую фазу.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
            db_session: Сессия базы данных
            partner: Партнер, которому отправляется уведомление
            user: Пользователь, у которого произошел переход фазы
            phase_info: Информация о новой фазе цикла
            
        Returns:
            True, если уведомление отправлено успешно
        """
        if not user.notification_enabled:
            return False
        
        try:
            # Форматируем краткую информацию о фазе с советами для партнера
            phase_data = PhaseFormatter.PHASE_DATA.get(phase_info.phase)
            if phase_data is None:
                return False
            
            message_text = (
                f"🔄 *Обновление фазы цикла*\n\n"
                f"{phase_data['emoji']} *{phase_data['name']}*\n"
                f"📅 День {phase_info.day_number}/{phase_info.cycle_length}\n\n"
                f"*Как себя вести мужчине:*\n"
                f"{phase_data['partner_advice']}"
            )
            
            await bot.send_message(
                chat_id=partner.telegram_id,
                text=message_text,
                parse_mode="Markdown"
            )
            
            # Сохраняем запись об уведомлении
            notification = Notification(
                user_id=user.id,
                partner_id=partner.id,
                notification_type=NotificationService.NOTIFICATION_TYPE_PARTNER_PHASE_CHANGE,
                sent_at=datetime.now()
            )
            db_session.add(notification)
            await db_session.flush()
            
            logger.info(f"Отправлено уведомление партнеру {partner.telegram_id} о смене фазы пользователя {user.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления партнеру {partner.telegram_id}: {e}")
            return False
    
    @staticmethod
    async def send_weekly_reminder(
        bot: Bot,
        db_session: AsyncSession,
        user: User
    ) -> bool:
        """
        Отправляет еженедельное напоминание пользователю о вводе дня цикла.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
            db_session: Сессия базы данных
            user: Пользователь, которому отправляется напоминание
            
        Returns:
            True, если уведомление отправлено успешно
        """
        if not user.notification_enabled:
            return False
        
        try:
            message_text = (
                "📅 *Напоминание*\n\n"
                "Не забудьте ввести текущий день цикла, чтобы получать "
                "актуальную информацию о вашей фазе и рекомендациях."
            )
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                parse_mode="Markdown"
            )
            
            # Сохраняем запись об уведомлении
            notification = Notification(
                user_id=user.id,
                notification_type=NotificationService.NOTIFICATION_TYPE_WEEKLY_REMINDER,
                sent_at=datetime.now()
            )
            db_session.add(notification)
            await db_session.flush()
            
            logger.info(f"Отправлено еженедельное напоминание пользователю {user.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания пользователю {user.telegram_id}: {e}")
            return False
    
    @staticmethod
    async def check_and_notify_phase_transitions(
        bot: Bot,
        db_session: AsyncSession
    ) -> None:
        """
        Проверяет всех пользователей на переход в новую фазу и отправляет уведомления.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
            db_session: Сессия базы данных
        """
        try:
            # Получаем всех пользователей с включенными уведомлениями
            stmt = select(User).where(User.notification_enabled == True)
            result = await db_session.execute(stmt)
            users = result.scalars().all()
            
            for user in users:
                if not user.last_period_date:
                    continue
                
                # Рассчитываем текущий день цикла
                current_day = CycleService.calculate_cycle_day(
                    user.last_period_date,
                    datetime.now()
                )
                
                if current_day is None:
                    continue
                
                # Получаем последнюю запись пользователя
                last_entry_stmt = (
                    select(CycleEntry)
                    .where(CycleEntry.user_id == user.id)
                    .order_by(CycleEntry.entry_date.desc())
                    .limit(1)
                )
                last_entry_result = await db_session.execute(last_entry_stmt)
                last_entry = last_entry_result.scalar_one_or_none()
                
                # Если нет записей, пропускаем
                if last_entry is None:
                    continue
                
                # Проверяем переход в новую фазу
                is_transition = CycleService.is_phase_transition(
                    current_day,
                    last_entry.day_number,
                    user.cycle_length or 28
                )
                
                if not is_transition:
                    continue
                
                # Получаем информацию о новой фазе
                phase_info = CycleService.get_phase_info(
                    current_day,
                    user.cycle_length or 28
                )
                
                if phase_info is None:
                    continue
                
                # Отправляем уведомление пользователю
                await NotificationService.send_phase_change_notification(
                    bot,
                    db_session,
                    user,
                    phase_info
                )
                
                # Отправляем уведомления партнерам
                partners = await PartnerService.get_partners(db_session, user.id)
                for partner in partners:
                    await NotificationService.send_partner_phase_change_notification(
                        bot,
                        db_session,
                        partner,
                        user,
                        phase_info
                    )
                
                await db_session.commit()
                
        except Exception as e:
            logger.error(f"Ошибка при проверке переходов фаз: {e}")
            await db_session.rollback()
    
    @staticmethod
    async def send_weekly_reminders_to_all(
        bot: Bot,
        db_session: AsyncSession
    ) -> None:
        """
        Отправляет еженедельные напоминания всем пользователям с включенными уведомлениями.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
            db_session: Сессия базы данных
        """
        try:
            # Получаем всех пользователей с включенными уведомлениями
            stmt = select(User).where(User.notification_enabled == True)
            result = await db_session.execute(stmt)
            users = result.scalars().all()
            
            for user in users:
                await NotificationService.send_weekly_reminder(
                    bot,
                    db_session,
                    user
                )
                await db_session.commit()
                
        except Exception as e:
            logger.error(f"Ошибка при отправке еженедельных напоминаний: {e}")
            await db_session.rollback()
