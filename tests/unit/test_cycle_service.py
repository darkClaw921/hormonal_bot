"""Unit тесты для cycle_service."""
import pytest
from datetime import datetime, timedelta

from services.cycle_service import (
    CycleService,
    CyclePhase,
    PhaseInfo,
)


class TestCalculateCycleDay:
    """Тесты для метода calculate_cycle_day."""
    
    def test_calculate_cycle_day_normal(self):
        """Тест расчета дня цикла в нормальных условиях."""
        last_period = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 5)
        
        result = CycleService.calculate_cycle_day(last_period, current_date)
        assert result == 5
    
    def test_calculate_cycle_day_first_day(self):
        """Тест расчета первого дня цикла."""
        last_period = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 1)
        
        result = CycleService.calculate_cycle_day(last_period, current_date)
        assert result == 1
    
    def test_calculate_cycle_day_without_current_date(self):
        """Тест расчета дня цикла без указания текущей даты."""
        last_period = datetime.now() - timedelta(days=5)
        
        result = CycleService.calculate_cycle_day(last_period)
        assert result == 6
    
    def test_calculate_cycle_day_future_date(self):
        """Тест расчета дня цикла с датой в будущем."""
        last_period = datetime(2024, 1, 5)
        current_date = datetime(2024, 1, 1)
        
        result = CycleService.calculate_cycle_day(last_period, current_date)
        assert result is None
    
    def test_calculate_cycle_day_over_limit(self):
        """Тест расчета дня цикла превышающего лимит в 35 дней."""
        last_period = datetime(2024, 1, 1)
        current_date = datetime(2024, 2, 10)  # 40 дней
        
        result = CycleService.calculate_cycle_day(last_period, current_date)
        assert result is None


class TestGetPhaseBoundaries:
    """Тесты для метода get_phase_boundaries."""
    
    def test_get_phase_boundaries_default(self):
        """Тест получения границ фаз для стандартного цикла (28 дней)."""
        boundaries = CycleService.get_phase_boundaries(28)
        
        assert boundaries[CyclePhase.MENSTRUAL] == (1, 5)
        assert boundaries[CyclePhase.POSTMENSTRUAL] == (6, 12)
        assert boundaries[CyclePhase.OVULATORY] == (13, 15)
        assert boundaries[CyclePhase.POSTOVULATORY] == (16, 24)
        assert boundaries[CyclePhase.PMS] == (25, 28)
    
    def test_get_phase_boundaries_short_cycle(self):
        """Тест получения границ фаз для короткого цикла (26 дней)."""
        boundaries = CycleService.get_phase_boundaries(26)
        
        # Проверяем, что границы адаптированы
        assert boundaries[CyclePhase.MENSTRUAL][0] == 1
        assert boundaries[CyclePhase.PMS][1] == 26
        assert boundaries[CyclePhase.PMS][0] >= 19  # Последние 7 дней
    
    def test_get_phase_boundaries_long_cycle(self):
        """Тест получения границ фаз для длинного цикла (35 дней)."""
        boundaries = CycleService.get_phase_boundaries(35)
        
        # Проверяем, что границы адаптированы
        assert boundaries[CyclePhase.MENSTRUAL][0] == 1
        assert boundaries[CyclePhase.PMS][1] == 35
        assert boundaries[CyclePhase.PMS][0] >= 28  # Последние 7 дней


class TestDeterminePhase:
    """Тесты для метода determine_phase."""
    
    def test_determine_phase_menstrual(self):
        """Тест определения менструальной фазы."""
        assert CycleService.determine_phase(1, 28) == CyclePhase.MENSTRUAL
        assert CycleService.determine_phase(3, 28) == CyclePhase.MENSTRUAL
        assert CycleService.determine_phase(5, 28) == CyclePhase.MENSTRUAL
    
    def test_determine_phase_postmenstrual(self):
        """Тест определения постменструальной фазы."""
        assert CycleService.determine_phase(6, 28) == CyclePhase.POSTMENSTRUAL
        assert CycleService.determine_phase(10, 28) == CyclePhase.POSTMENSTRUAL
        assert CycleService.determine_phase(12, 28) == CyclePhase.POSTMENSTRUAL
    
    def test_determine_phase_ovulatory(self):
        """Тест определения овуляторной фазы."""
        assert CycleService.determine_phase(13, 28) == CyclePhase.OVULATORY
        assert CycleService.determine_phase(14, 28) == CyclePhase.OVULATORY
        assert CycleService.determine_phase(15, 28) == CyclePhase.OVULATORY
    
    def test_determine_phase_postovulatory(self):
        """Тест определения постовуляторной фазы."""
        assert CycleService.determine_phase(16, 28) == CyclePhase.POSTOVULATORY
        assert CycleService.determine_phase(20, 28) == CyclePhase.POSTOVULATORY
        assert CycleService.determine_phase(24, 28) == CyclePhase.POSTOVULATORY
    
    def test_determine_phase_pms(self):
        """Тест определения фазы ПМС."""
        assert CycleService.determine_phase(25, 28) == CyclePhase.PMS
        assert CycleService.determine_phase(27, 28) == CyclePhase.PMS
        assert CycleService.determine_phase(28, 28) == CyclePhase.PMS
    
    def test_determine_phase_invalid_day(self):
        """Тест определения фазы для невалидного дня."""
        assert CycleService.determine_phase(0, 28) is None
        assert CycleService.determine_phase(36, 28) is None
        assert CycleService.determine_phase(-1, 28) is None
    
    def test_determine_phase_custom_cycle_length(self):
        """Тест определения фазы для нестандартной длины цикла."""
        # Для цикла 30 дней
        assert CycleService.determine_phase(1, 30) == CyclePhase.MENSTRUAL
        assert CycleService.determine_phase(28, 30) == CyclePhase.PMS
        assert CycleService.determine_phase(30, 30) == CyclePhase.PMS


class TestGetPhaseInfo:
    """Тесты для метода get_phase_info."""
    
    def test_get_phase_info_valid(self):
        """Тест получения информации о фазе для валидного дня."""
        phase_info = CycleService.get_phase_info(14, 28)
        
        assert isinstance(phase_info, PhaseInfo)
        assert phase_info.phase == CyclePhase.OVULATORY
        assert phase_info.day_number == 14
        assert phase_info.phase_start_day == 13
        assert phase_info.phase_end_day == 15
        assert phase_info.cycle_length == 28
    
    def test_get_phase_info_invalid_day(self):
        """Тест получения информации о фазе для невалидного дня."""
        assert CycleService.get_phase_info(0, 28) is None
        assert CycleService.get_phase_info(36, 28) is None
    
    def test_get_phase_info_all_phases(self):
        """Тест получения информации для всех фаз."""
        phases_to_test = [
            (3, CyclePhase.MENSTRUAL),
            (9, CyclePhase.POSTMENSTRUAL),
            (14, CyclePhase.OVULATORY),
            (20, CyclePhase.POSTOVULATORY),
            (27, CyclePhase.PMS),
        ]
        
        for day, expected_phase in phases_to_test:
            phase_info = CycleService.get_phase_info(day, 28)
            assert phase_info is not None
            assert phase_info.phase == expected_phase
            assert phase_info.day_number == day


class TestIsPhaseTransition:
    """Тесты для метода is_phase_transition."""
    
    def test_is_phase_transition_true(self):
        """Тест определения перехода в новую фазу."""
        # Переход с дня 5 (менструальная) на день 6 (постменструальная)
        assert CycleService.is_phase_transition(6, 5, 28) is True
        
        # Переход с дня 12 (постменструальная) на день 13 (овуляторная)
        assert CycleService.is_phase_transition(13, 12, 28) is True
        
        # Переход с дня 15 (овуляторная) на день 16 (постовуляторная)
        assert CycleService.is_phase_transition(16, 15, 28) is True
    
    def test_is_phase_transition_false(self):
        """Тест определения отсутствия перехода в новую фазу."""
        # Остаемся в той же фазе
        assert CycleService.is_phase_transition(3, 2, 28) is False
        assert CycleService.is_phase_transition(10, 9, 28) is False
        assert CycleService.is_phase_transition(20, 19, 28) is False
    
    def test_is_phase_transition_no_previous_day(self):
        """Тест определения перехода без предыдущего дня."""
        assert CycleService.is_phase_transition(5, None, 28) is False
    
    def test_is_phase_transition_custom_cycle_length(self):
        """Тест определения перехода для нестандартной длины цикла."""
        # Для цикла 30 дней
        assert CycleService.is_phase_transition(6, 5, 30) is True
        assert CycleService.is_phase_transition(10, 9, 30) is False
