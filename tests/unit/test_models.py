"""Unit тесты для моделей базы данных."""
import pytest
from datetime import datetime

from database.models import User, Partner, CycleEntry, Notification


class TestUserModel:
    """Тесты для модели User."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db_session):
        """Тест создания пользователя."""
        user = User(
            telegram_id=111222333,
            username="new_user",
            cycle_length=30,
            notification_enabled=True,
            notification_time="10:00",
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        
        assert user.id is not None
        assert user.telegram_id == 111222333
        assert user.username == "new_user"
        assert user.cycle_length == 30
        assert user.notification_enabled is True
        assert user.notification_time == "10:00"
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_user_defaults(self, test_db_session):
        """Тест значений по умолчанию для пользователя."""
        user = User(telegram_id=999888777)
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        
        assert user.cycle_length == 28
        assert user.notification_enabled is True
        assert user.notification_time == "09:00"
        assert user.last_period_date is None
    
    @pytest.mark.asyncio
    async def test_user_relationships(self, test_db_session, test_user):
        """Тест связей пользователя с другими моделями."""
        # Создаем партнера
        partner = Partner(
            telegram_id=555666777,
            user_id=test_user.id,
        )
        test_db_session.add(partner)
        
        # Создаем запись цикла
        cycle_entry = CycleEntry(
            user_id=test_user.id,
            day_number=5,
            entry_date=datetime.now(),
            phase="менструальная",
        )
        test_db_session.add(cycle_entry)
        
        # Создаем уведомление
        notification = Notification(
            user_id=test_user.id,
            notification_type="phase_change",
        )
        test_db_session.add(notification)
        
        await test_db_session.commit()
        await test_db_session.refresh(test_user)
        
        # Используем awaitable_attrs для async relationships
        assert len(await test_user.awaitable_attrs.partners) == 1
        assert len(await test_user.awaitable_attrs.cycle_entries) == 1
        assert len(await test_user.awaitable_attrs.notifications) == 1


class TestPartnerModel:
    """Тесты для модели Partner."""
    
    @pytest.mark.asyncio
    async def test_create_partner(self, test_db_session, test_user):
        """Тест создания партнера."""
        partner = Partner(
            telegram_id=444555666,
            username="partner_user",
            user_id=test_user.id,
        )
        test_db_session.add(partner)
        await test_db_session.commit()
        await test_db_session.refresh(partner)
        
        assert partner.id is not None
        assert partner.telegram_id == 444555666
        assert partner.username == "partner_user"
        assert partner.user_id == test_user.id
        assert partner.created_at is not None
    
    @pytest.mark.asyncio
    async def test_partner_user_relationship(self, test_db_session, test_user):
        """Тест связи партнера с пользователем."""
        partner = Partner(
            telegram_id=333444555,
            user_id=test_user.id,
        )
        test_db_session.add(partner)
        await test_db_session.commit()
        await test_db_session.refresh(partner)
        
        assert partner.user.id == test_user.id
        assert partner.user.telegram_id == test_user.telegram_id
    
    @pytest.mark.asyncio
    async def test_partner_cascade_delete(self, test_db_session, test_user):
        """Тест каскадного удаления партнера при удалении пользователя."""
        partner = Partner(
            telegram_id=222333444,
            user_id=test_user.id,
        )
        test_db_session.add(partner)
        await test_db_session.commit()
        
        partner_id = partner.id
        
        # Удаляем пользователя
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
        # Проверяем, что партнер тоже удален
        deleted_partner = await test_db_session.get(Partner, partner_id)
        assert deleted_partner is None


class TestCycleEntryModel:
    """Тесты для модели CycleEntry."""
    
    @pytest.mark.asyncio
    async def test_create_cycle_entry(self, test_db_session, test_user):
        """Тест создания записи цикла."""
        entry_date = datetime(2024, 1, 15)
        cycle_entry = CycleEntry(
            user_id=test_user.id,
            day_number=5,
            entry_date=entry_date,
            phase="менструальная",
        )
        test_db_session.add(cycle_entry)
        await test_db_session.commit()
        await test_db_session.refresh(cycle_entry)
        
        assert cycle_entry.id is not None
        assert cycle_entry.user_id == test_user.id
        assert cycle_entry.day_number == 5
        assert cycle_entry.entry_date == entry_date
        assert cycle_entry.phase == "менструальная"
        assert cycle_entry.created_at is not None
    
    @pytest.mark.asyncio
    async def test_cycle_entry_user_relationship(self, test_db_session, test_user):
        """Тест связи записи цикла с пользователем."""
        cycle_entry = CycleEntry(
            user_id=test_user.id,
            day_number=10,
            entry_date=datetime.now(),
            phase="постменструальная",
        )
        test_db_session.add(cycle_entry)
        await test_db_session.commit()
        await test_db_session.refresh(cycle_entry)
        
        assert cycle_entry.user.id == test_user.id
        assert cycle_entry.user.telegram_id == test_user.telegram_id
    
    @pytest.mark.asyncio
    async def test_cycle_entry_cascade_delete(self, test_db_session, test_user):
        """Тест каскадного удаления записей цикла при удалении пользователя."""
        cycle_entry = CycleEntry(
            user_id=test_user.id,
            day_number=15,
            entry_date=datetime.now(),
            phase="овуляторная",
        )
        test_db_session.add(cycle_entry)
        await test_db_session.commit()
        
        entry_id = cycle_entry.id
        
        # Удаляем пользователя
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
        # Проверяем, что запись цикла тоже удалена
        deleted_entry = await test_db_session.get(CycleEntry, entry_id)
        assert deleted_entry is None


class TestNotificationModel:
    """Тесты для модели Notification."""
    
    @pytest.mark.asyncio
    async def test_create_notification_for_user(self, test_db_session, test_user):
        """Тест создания уведомления для пользователя."""
        notification = Notification(
            user_id=test_user.id,
            notification_type="phase_change",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)
        
        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.partner_id is None
        assert notification.notification_type == "phase_change"
        assert notification.sent_at is not None
    
    @pytest.mark.asyncio
    async def test_create_notification_for_partner(
        self, test_db_session, test_user, test_partner
    ):
        """Тест создания уведомления для партнера."""
        notification = Notification(
            user_id=test_user.id,
            partner_id=test_partner.id,
            notification_type="phase_change",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)
        
        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.partner_id == test_partner.id
        assert notification.notification_type == "phase_change"
    
    @pytest.mark.asyncio
    async def test_notification_relationships(
        self, test_db_session, test_user, test_partner
    ):
        """Тест связей уведомления с пользователем и партнером."""
        notification = Notification(
            user_id=test_user.id,
            partner_id=test_partner.id,
            notification_type="weekly_reminder",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)
        
        assert notification.user.id == test_user.id
        assert notification.partner.id == test_partner.id
    
    @pytest.mark.asyncio
    async def test_notification_cascade_delete(self, test_db_session, test_user):
        """Тест каскадного удаления уведомлений при удалении пользователя."""
        notification = Notification(
            user_id=test_user.id,
            notification_type="phase_change",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        
        notification_id = notification.id
        
        # Удаляем пользователя
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
        # Проверяем, что уведомление тоже удалено
        deleted_notification = await test_db_session.get(Notification, notification_id)
        assert deleted_notification is None
    
    @pytest.mark.asyncio
    async def test_notification_cascade_delete_partner(
        self, test_db_session, test_user, test_partner
    ):
        """Тест каскадного удаления уведомлений при удалении партнера."""
        notification = Notification(
            user_id=test_user.id,
            partner_id=test_partner.id,
            notification_type="phase_change",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        
        notification_id = notification.id
        
        # Удаляем партнера
        await test_db_session.delete(test_partner)
        await test_db_session.commit()
        
        # Проверяем, что уведомление тоже удалено
        deleted_notification = await test_db_session.get(Notification, notification_id)
        assert deleted_notification is None
