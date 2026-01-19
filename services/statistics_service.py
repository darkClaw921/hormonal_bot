"""Сервис для расчета статистики менструального цикла."""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CycleEntry, User
from services.cycle_service import CyclePhase


@dataclass
class CycleStats:
    """Статистика одного цикла."""
    start_date: datetime
    end_date: Optional[datetime]
    length: Optional[int]  # Длина цикла в днях (None если цикл не завершен)
    entries_count: int  # Количество записей в цикле


@dataclass
class UserStatistics:
    """Общая статистика пользователя."""
    total_cycles: int  # Общее количество завершенных циклов
    average_cycle_length: Optional[float]  # Средняя длина цикла (None если нет завершенных циклов)
    current_cycle_day: Optional[int]  # Текущий день цикла
    current_phase: Optional[str]  # Текущая фаза цикла
    cycles_history: list[CycleStats]  # История циклов
    total_entries: int  # Общее количество записей


class StatisticsService:
    """Сервис для расчета статистики менструального цикла."""
    
    @staticmethod
    async def get_user_statistics(
        user: User,
        db_session: AsyncSession
    ) -> UserStatistics:
        """
        Получает статистику пользователя.
        
        Args:
            user: Пользователь
            db_session: Сессия базы данных
            
        Returns:
            Статистика пользователя
        """
        # Получаем все записи пользователя, отсортированные по дате
        stmt = (
            select(CycleEntry)
            .where(CycleEntry.user_id == user.id)
            .order_by(CycleEntry.entry_date.asc())
        )
        result = await db_session.execute(stmt)
        entries = result.scalars().all()
        
        if not entries:
            return UserStatistics(
                total_cycles=0,
                average_cycle_length=None,
                current_cycle_day=None,
                current_phase=None,
                cycles_history=[],
                total_entries=0
            )
        
        # Определяем циклы
        cycles = StatisticsService._identify_cycles(entries, user.cycle_length)
        
        # Рассчитываем среднюю длину цикла
        completed_cycles = [c for c in cycles if c.length is not None]
        average_length = None
        if completed_cycles:
            average_length = sum(c.length for c in completed_cycles) / len(completed_cycles)
        
        # Определяем текущий день цикла и фазу
        last_entry = entries[-1]
        current_cycle_day = last_entry.day_number
        current_phase = last_entry.phase
        
        return UserStatistics(
            total_cycles=len(completed_cycles),
            average_cycle_length=average_length,
            current_cycle_day=current_cycle_day,
            current_phase=current_phase,
            cycles_history=cycles,
            total_entries=len(entries)
        )
    
    @staticmethod
    def _identify_cycles(
        entries: list[CycleEntry],
        cycle_length: int
    ) -> list[CycleStats]:
        """
        Определяет циклы из записей.
        
        Новый цикл начинается когда:
        1. day_number возвращается к 1-3 (начало менструации)
        2. Или day_number значительно меньше предыдущего (например, было 25, стало 2)
        
        Args:
            entries: Список записей, отсортированных по дате
            cycle_length: Длина цикла пользователя
            
        Returns:
            Список статистики циклов
        """
        if not entries:
            return []
        
        cycles: list[CycleStats] = []
        current_cycle_start: Optional[datetime] = None
        current_cycle_entries: list[CycleEntry] = []
        previous_day: Optional[int] = None
        
        for entry in entries:
            # Определяем начало нового цикла
            is_new_cycle = False
            
            if previous_day is None:
                # Первая запись - начало первого цикла
                is_new_cycle = True
            elif entry.day_number <= 3 and previous_day > cycle_length - 5:
                # Переход от конца цикла к началу (например, с 25 на 2)
                is_new_cycle = True
            elif entry.day_number <= 3 and previous_day is not None and previous_day <= 3:
                # Две записи подряд в начале цикла - новая менструация
                # Проверяем, что прошло достаточно времени (минимум 20 дней)
                if current_cycle_start:
                    days_between = (entry.entry_date - current_cycle_start).days
                    if days_between >= 20:
                        is_new_cycle = True
            
            if is_new_cycle:
                # Сохраняем предыдущий цикл
                if current_cycle_start and current_cycle_entries:
                    cycle_length_days = None
                    if len(current_cycle_entries) > 1:
                        # Длина цикла = разница между первой и последней записью + последний день
                        first_day = current_cycle_entries[0].day_number
                        last_day = current_cycle_entries[-1].day_number
                        # Если последний день меньше первого, значит цикл завершился
                        if last_day < first_day:
                            cycle_length_days = last_day + (cycle_length - first_day) + 1
                        else:
                            cycle_length_days = last_day - first_day + 1
                    
                    cycles.append(CycleStats(
                        start_date=current_cycle_start,
                        end_date=current_cycle_entries[-1].entry_date,
                        length=cycle_length_days,
                        entries_count=len(current_cycle_entries)
                    ))
                
                # Начинаем новый цикл
                current_cycle_start = entry.entry_date
                current_cycle_entries = [entry]
            else:
                # Продолжаем текущий цикл
                if current_cycle_start is None:
                    current_cycle_start = entry.entry_date
                current_cycle_entries.append(entry)
            
            previous_day = entry.day_number
        
        # Сохраняем последний цикл (может быть незавершенным)
        if current_cycle_start and current_cycle_entries:
            cycles.append(CycleStats(
                start_date=current_cycle_start,
                end_date=current_cycle_entries[-1].entry_date,
                length=None,  # Текущий цикл еще не завершен
                entries_count=len(current_cycle_entries)
            ))
        
        return cycles
    
    @staticmethod
    def format_statistics(stats: UserStatistics) -> str:
        """
        Форматирует статистику для отображения пользователю.
        
        Args:
            stats: Статистика пользователя
            
        Returns:
            Отформатированный текст статистики
        """
        lines = []
        
        # Текущий статус
        if stats.current_cycle_day:
            lines.append(f"📅 **Текущий день цикла:** {stats.current_cycle_day}")
            if stats.current_phase:
                phase_name = stats.current_phase.capitalize()
                lines.append(f"🔄 **Текущая фаза:** {phase_name}")
        else:
            lines.append("📅 У вас пока нет записей о цикле.")
        
        lines.append("")  # Пустая строка
        
        # Общая статистика
        if stats.total_cycles > 0:
            lines.append(f"📊 **Завершенных циклов:** {stats.total_cycles}")
            if stats.average_cycle_length:
                avg_length = round(stats.average_cycle_length, 1)
                lines.append(f"📈 **Средняя длина цикла:** {avg_length} дней")
        else:
            lines.append("📊 У вас пока нет завершенных циклов.")
        
        lines.append("")  # Пустая строка
        
        # История циклов (последние 5)
        if stats.cycles_history:
            lines.append("📋 **История циклов:**")
            recent_cycles = stats.cycles_history[-5:]  # Последние 5 циклов
            for i, cycle in enumerate(reversed(recent_cycles), 1):
                start_date_str = cycle.start_date.strftime("%d.%m.%Y")
                if cycle.length:
                    lines.append(
                        f"{i}. {start_date_str} - {cycle.length} дней "
                        f"({cycle.entries_count} записей)"
                    )
                else:
                    lines.append(
                        f"{i}. {start_date_str} - текущий цикл "
                        f"({cycle.entries_count} записей)"
                    )
        else:
            lines.append("📋 История циклов пуста.")
        
        lines.append("")  # Пустая строка
        lines.append(f"📝 **Всего записей:** {stats.total_entries}")
        
        return "\n".join(lines)
