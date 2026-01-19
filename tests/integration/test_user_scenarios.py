"""Интеграционные тесты для основных сценариев использования."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from database.models import User, CycleEntry, Partner
from services.cycle_service import CycleService
from services.partner_service import PartnerService
from services.statistics_service import StatisticsService


class TestUserRegistrationScenario:
    """Тесты сценария регистрации пользователя."""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, test_db_session):
        """Тест регистрации нового пользователя."""
        # Создаем пользователя
        user = User(
            telegram_id=111111111,
            username="new_user",
            cycle_length=28,
            notification_enabled=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        
        # Проверяем, что пользователь создан
        assert user.id is not None
        assert user.telegram_id == 111111111
        assert user.username == "new_user"
        
        # Проверяем значения по умолчанию
        assert user.cycle_length == 28
        assert user.notification_enabled is True
        assert user.notification_time == "09:00"
    
    @pytest.mark.asyncio
    async def test_user_registration_with_last_period_date(self, test_db_session):
        """Тест регистрации пользователя с указанием даты последней менструации."""
        from datetime import timedelta
        # Используем дату несколько дней назад для корректного расчета
        last_period = datetime.now() - timedelta(days=5)
        user = User(
            telegram_id=222222222,
            username="user_with_period",
            cycle_length=30,
            last_period_date=last_period,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        
        assert user.last_period_date == last_period
        
        # Проверяем расчет текущего дня цикла
        current_day = CycleService.calculate_cycle_day(
            user.last_period_date,
            datetime.now()
        )
        assert current_day is not None
        assert 1 <= current_day <= 35


class TestCycleEntryScenario:
    """Тесты сценария ввода дня цикла."""
    
    @pytest.mark.asyncio
    async def test_cycle_entry_creation(self, test_db_session, test_user):
        """Тест создания записи о дне цикла."""
        entry_date = datetime(2024, 1, 15)
        day_number = 5
        
        # Определяем фазу цикла
        phase = CycleService.determine_phase(day_number, test_user.cycle_length)
        assert phase is not None
        
        # Создаем запись
        cycle_entry = CycleEntry(
            user_id=test_user.id,
            day_number=day_number,
            entry_date=entry_date,
            phase=phase.value,
        )
        test_db_session.add(cycle_entry)
        await test_db_session.commit()
        await test_db_session.refresh(cycle_entry)
        
        assert cycle_entry.id is not None
        assert cycle_entry.user_id == test_user.id
        assert cycle_entry.day_number == day_number
        assert cycle_entry.phase == phase.value
    
    @pytest.mark.asyncio
    async def test_multiple_cycle_entries(self, test_db_session, test_user):
        """Тест создания нескольких записей цикла."""
        base_date = datetime(2024, 1, 1)
        
        # Создаем записи для разных дней цикла
        entries_data = [
            (1, "менструальная"),
            (5, "менструальная"),
            (10, "постменструальная"),
            (14, "овуляторная"),
            (20, "постовуляторная"),
            (27, "пмс"),
        ]
        
        for day_number, expected_phase in entries_data:
            entry_date = base_date + timedelta(days=day_number - 1)
            cycle_entry = CycleEntry(
                user_id=test_user.id,
                day_number=day_number,
                entry_date=entry_date,
                phase=expected_phase,
            )
            test_db_session.add(cycle_entry)
        
        await test_db_session.commit()
        
        # Проверяем, что все записи созданы
        stmt = select(CycleEntry).where(CycleEntry.user_id == test_user.id)
        result = await test_db_session.execute(stmt)
        entries = result.scalars().all()
        
        assert len(entries) == len(entries_data)
        
        # Проверяем статистику
        stats = await StatisticsService.get_user_statistics(test_user, test_db_session)
        assert stats.total_entries == len(entries_data)
        assert stats.current_cycle_day == 27
        assert stats.current_phase == "пмс"
    
    @pytest.mark.asyncio
    async def test_phase_transition_detection(self, test_db_session, test_user):
        """Тест определения перехода в новую фазу."""
        base_date = datetime(2024, 1, 1)
        
        # Создаем записи до и после перехода фазы
        entry1 = CycleEntry(
            user_id=test_user.id,
            day_number=5,  # Менструальная фаза
            entry_date=base_date + timedelta(days=4),
            phase="менструальная",
        )
        test_db_session.add(entry1)
        await test_db_session.commit()
        
        entry2 = CycleEntry(
            user_id=test_user.id,
            day_number=6,  # Постменструальная фаза
            entry_date=base_date + timedelta(days=5),
            phase="постменструальная",
        )
        test_db_session.add(entry2)
        await test_db_session.commit()
        
        # Проверяем переход фазы
        is_transition = CycleService.is_phase_transition(6, 5, test_user.cycle_length)
        assert is_transition is True


class TestPartnerManagementScenario:
    """Тесты сценария управления партнерами."""
    
    @pytest.mark.asyncio
    async def test_add_partner(self, test_db_session, test_user):
        """Тест добавления партнера."""
        partner = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=999888777,
            partner_username="partner_user",
        )
        
        assert partner is not None
        assert partner.telegram_id == 999888777
        assert partner.username == "partner_user"
        assert partner.user_id == test_user.id
        
        await test_db_session.commit()
        await test_db_session.refresh(partner)
        
        # Проверяем связь
        assert partner.user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_add_duplicate_partner(self, test_db_session, test_user):
        """Тест попытки добавить дубликат партнера."""
        # Добавляем партнера первый раз
        partner1 = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=888777666,
        )
        assert partner1 is not None
        await test_db_session.commit()
        
        # Пытаемся добавить того же партнера второй раз
        partner2 = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=888777666,
        )
        assert partner2 is None
    
    @pytest.mark.asyncio
    async def test_add_self_as_partner(self, test_db_session, test_user):
        """Тест попытки добавить себя в качестве партнера."""
        partner = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=test_user.telegram_id,
        )
        assert partner is None
    
    @pytest.mark.asyncio
    async def test_remove_partner(self, test_db_session, test_user):
        """Тест удаления партнера."""
        # Добавляем партнера
        partner = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=777666555,
        )
        assert partner is not None
        await test_db_session.commit()
        await test_db_session.refresh(partner)
        
        partner_id = partner.id
        
        # Удаляем партнера
        result = await PartnerService.remove_partner(
            test_db_session,
            test_user.id,
            partner_id,
        )
        assert result is True
        await test_db_session.commit()
        
        # Проверяем, что партнер удален
        deleted_partner = await test_db_session.get(Partner, partner_id)
        assert deleted_partner is None
    
    @pytest.mark.asyncio
    async def test_get_partners_list(self, test_db_session, test_user):
        """Тест получения списка партнеров."""
        # Добавляем несколько партнеров
        partner1 = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=111222333,
        )
        partner2 = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=444555666,
        )
        await test_db_session.commit()
        
        # Получаем список партнеров
        partners = await PartnerService.get_partners(test_db_session, test_user.id)
        
        assert len(partners) == 2
        partner_ids = {p.id for p in partners}
        assert partner1.id in partner_ids
        assert partner2.id in partner_ids
    
    @pytest.mark.asyncio
    async def test_get_user_by_partner_telegram_id(self, test_db_session, test_user):
        """Тест получения пользователя по Telegram ID партнера."""
        # Добавляем партнера
        partner = await PartnerService.add_partner(
            test_db_session,
            test_user.id,
            partner_telegram_id=333444555,
        )
        await test_db_session.commit()
        
        # Получаем пользователя по Telegram ID партнера
        user = await PartnerService.get_user_by_partner_telegram_id(
            test_db_session,
            333444555,
        )
        
        assert user is not None
        assert user.id == test_user.id
        assert user.telegram_id == test_user.telegram_id


class TestStatisticsScenario:
    """Тесты сценария получения статистики."""
    
    @pytest.mark.asyncio
    async def test_statistics_empty_user(self, test_db_session, test_user):
        """Тест статистики для пользователя без записей."""
        stats = await StatisticsService.get_user_statistics(test_user, test_db_session)
        
        assert stats.total_cycles == 0
        assert stats.average_cycle_length is None
        assert stats.current_cycle_day is None
        assert stats.current_phase is None
        assert len(stats.cycles_history) == 0
        assert stats.total_entries == 0
    
    @pytest.mark.asyncio
    async def test_statistics_with_entries(self, test_db_session, test_user):
        """Тест статистики для пользователя с записями."""
        base_date = datetime(2024, 1, 1)
        
        # Создаем записи для одного цикла
        entries_data = [
            (1, "менструальная"),
            (5, "менструальная"),
            (10, "постменструальная"),
            (15, "овуляторная"),
            (20, "постовуляторная"),
            (28, "пмс"),
        ]
        
        for day_number, phase in entries_data:
            entry_date = base_date + timedelta(days=day_number - 1)
            cycle_entry = CycleEntry(
                user_id=test_user.id,
                day_number=day_number,
                entry_date=entry_date,
                phase=phase,
            )
            test_db_session.add(cycle_entry)
        
        await test_db_session.commit()
        
        # Получаем статистику
        stats = await StatisticsService.get_user_statistics(test_user, test_db_session)
        
        assert stats.total_entries == len(entries_data)
        assert stats.current_cycle_day == 28
        assert stats.current_phase == "пмс"
        assert len(stats.cycles_history) > 0
