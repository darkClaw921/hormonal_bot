"""Сервис для работы с партнерами."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Partner, User


class PartnerService:
    """Сервис для работы с партнерами пользователя."""
    
    @staticmethod
    async def add_partner(
        db_session: AsyncSession,
        user_id: int,
        partner_telegram_id: int,
        partner_username: Optional[str] = None
    ) -> Optional[Partner]:
        """
        Добавляет партнера к пользователю.
        
        Args:
            db_session: Сессия базы данных
            user_id: ID пользователя
            partner_telegram_id: Telegram ID партнера
            partner_username: Username партнера (опционально)
            
        Returns:
            Созданный объект Partner или None, если партнер уже существует
        """
        # Проверяем, существует ли уже такой партнер
        stmt = select(Partner).where(Partner.telegram_id == partner_telegram_id)
        result = await db_session.execute(stmt)
        existing_partner = result.scalar_one_or_none()
        
        if existing_partner:
            return None
        
        # Проверяем, не является ли партнер самим пользователем
        stmt = select(User).where(User.telegram_id == partner_telegram_id)
        result = await db_session.execute(stmt)
        user_as_partner = result.scalar_one_or_none()
        
        if user_as_partner and user_as_partner.id == user_id:
            return None
        
        # Создаем нового партнера
        partner = Partner(
            telegram_id=partner_telegram_id,
            username=partner_username,
            user_id=user_id
        )
        db_session.add(partner)
        await db_session.flush()
        
        return partner
    
    @staticmethod
    async def remove_partner(
        db_session: AsyncSession,
        user_id: int,
        partner_id: int
    ) -> bool:
        """
        Удаляет партнера у пользователя.
        
        Args:
            db_session: Сессия базы данных
            user_id: ID пользователя
            partner_id: ID партнера для удаления
            
        Returns:
            True, если партнер был удален, False если не найден
        """
        stmt = select(Partner).where(
            Partner.id == partner_id,
            Partner.user_id == user_id
        )
        result = await db_session.execute(stmt)
        partner = result.scalar_one_or_none()
        
        if partner is None:
            return False
        
        await db_session.delete(partner)
        await db_session.flush()
        
        return True
    
    @staticmethod
    async def get_partners(
        db_session: AsyncSession,
        user_id: int
    ) -> list[Partner]:
        """
        Получает список всех партнеров пользователя.
        
        Args:
            db_session: Сессия базы данных
            user_id: ID пользователя
            
        Returns:
            Список партнеров пользователя
        """
        stmt = select(Partner).where(Partner.user_id == user_id)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_partner_by_telegram_id(
        db_session: AsyncSession,
        partner_telegram_id: int
    ) -> Optional[Partner]:
        """
        Получает партнера по его Telegram ID.
        
        Args:
            db_session: Сессия базы данных
            partner_telegram_id: Telegram ID партнера
            
        Returns:
            Объект Partner или None, если не найден
        """
        stmt = select(Partner).where(Partner.telegram_id == partner_telegram_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_partner_telegram_id(
        db_session: AsyncSession,
        partner_telegram_id: int
    ) -> Optional[User]:
        """
        Получает пользователя по Telegram ID его партнера.
        
        Args:
            db_session: Сессия базы данных
            partner_telegram_id: Telegram ID партнера
            
        Returns:
            Объект User или None, если партнер не найден
        """
        stmt = select(Partner).where(Partner.telegram_id == partner_telegram_id)
        result = await db_session.execute(stmt)
        partner = result.scalar_one_or_none()
        
        if partner is None:
            return None
        
        # Загружаем связанного пользователя
        await db_session.refresh(partner, ["user"])
        return partner.user
