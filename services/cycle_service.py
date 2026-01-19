"""Сервис для расчета фаз менструального цикла."""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class CyclePhase(str, Enum):
    """Фазы менструального цикла."""
    MENSTRUAL = "менструальная"
    POSTMENSTRUAL = "постменструальная"
    OVULATORY = "овуляторная"
    POSTOVULATORY = "постовуляторная"
    PMS = "пмс"


@dataclass
class PhaseInfo:
    """Информация о фазе цикла."""
    phase: CyclePhase
    day_number: int
    phase_start_day: int
    phase_end_day: int
    cycle_length: int


class CycleService:
    """Сервис для расчета фаз менструального цикла."""
    
    # Стандартные границы фаз для цикла длиной 28 дней
    DEFAULT_PHASE_BOUNDARIES = {
        CyclePhase.MENSTRUAL: (1, 5),
        CyclePhase.POSTMENSTRUAL: (6, 12),
        CyclePhase.OVULATORY: (13, 15),
        CyclePhase.POSTOVULATORY: (16, 24),
        CyclePhase.PMS: (25, 28),
    }
    
    @staticmethod
    def calculate_cycle_day(
        last_period_date: datetime,
        current_date: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Рассчитывает день цикла от последней менструации.
        
        Args:
            last_period_date: Дата начала последней менструации
            current_date: Текущая дата (по умолчанию datetime.now())
            
        Returns:
            Номер дня цикла (1-35) или None, если дата некорректна
        """
        if current_date is None:
            current_date = datetime.now()
        
        if last_period_date > current_date:
            return None
        
        delta = current_date - last_period_date
        day_number = delta.days + 1
        
        # Ограничиваем максимальным значением 35 дней
        if day_number > 35:
            return None
        
        return day_number
    
    @staticmethod
    def get_phase_boundaries(cycle_length: int = 28) -> dict[CyclePhase, tuple[int, int]]:
        """
        Получает границы фаз для заданной длины цикла.
        
        Args:
            cycle_length: Длина цикла в днях (по умолчанию 28)
            
        Returns:
            Словарь с границами фаз
        """
        if cycle_length == 28:
            return CycleService.DEFAULT_PHASE_BOUNDARIES.copy()
        
        # Адаптируем границы под длину цикла
        # Используем пропорциональное масштабирование
        scale = cycle_length / 28.0
        
        boundaries = {}
        for phase, (start, end) in CycleService.DEFAULT_PHASE_BOUNDARIES.items():
            new_start = max(1, int(start * scale))
            new_end = min(cycle_length, int(end * scale))
            
            # Для ПМС используем последние 3-7 дней цикла
            if phase == CyclePhase.PMS:
                new_start = max(cycle_length - 7, 1)
                new_end = cycle_length
            # Для овуляторной фазы оставляем 2-4 дня в середине
            elif phase == CyclePhase.OVULATORY:
                mid_point = cycle_length // 2
                new_start = max(mid_point - 1, 1)
                new_end = min(mid_point + 2, cycle_length)
            
            boundaries[phase] = (new_start, new_end)
        
        return boundaries
    
    @staticmethod
    def determine_phase(day_number: int, cycle_length: int = 28) -> Optional[CyclePhase]:
        """
        Определяет фазу цикла по номеру дня.
        
        Args:
            day_number: Номер дня цикла (1-35)
            cycle_length: Длина цикла в днях (по умолчанию 28)
            
        Returns:
            Фаза цикла или None, если день вне диапазона
        """
        if day_number < 1 or day_number > 35:
            return None
        
        boundaries = CycleService.get_phase_boundaries(cycle_length)
        
        # Проверяем фазы в порядке приоритета (от более специфичных к общим)
        for phase in [CyclePhase.OVULATORY, CyclePhase.PMS, CyclePhase.MENSTRUAL, 
                      CyclePhase.POSTMENSTRUAL, CyclePhase.POSTOVULATORY]:
            start, end = boundaries[phase]
            if start <= day_number <= end:
                return phase
        
        return None
    
    @staticmethod
    def get_phase_info(day_number: int, cycle_length: int = 28) -> Optional[PhaseInfo]:
        """
        Получает полную информацию о фазе цикла.
        
        Args:
            day_number: Номер дня цикла (1-35)
            cycle_length: Длина цикла в днях (по умолчанию 28)
            
        Returns:
            Информация о фазе или None, если день вне диапазона
        """
        phase = CycleService.determine_phase(day_number, cycle_length)
        if phase is None:
            return None
        
        boundaries = CycleService.get_phase_boundaries(cycle_length)
        start, end = boundaries[phase]
        
        return PhaseInfo(
            phase=phase,
            day_number=day_number,
            phase_start_day=start,
            phase_end_day=end,
            cycle_length=cycle_length
        )
    
    @staticmethod
    def is_phase_transition(
        current_day: int,
        previous_day: Optional[int],
        cycle_length: int = 28
    ) -> bool:
        """
        Определяет, произошел ли переход в новую фазу.
        
        Args:
            current_day: Текущий день цикла
            previous_day: Предыдущий день цикла (может быть None)
            cycle_length: Длина цикла в днях
            
        Returns:
            True, если произошел переход в новую фазу
        """
        if previous_day is None:
            return False
        
        current_phase = CycleService.determine_phase(current_day, cycle_length)
        previous_phase = CycleService.determine_phase(previous_day, cycle_length)
        
        return current_phase != previous_phase
