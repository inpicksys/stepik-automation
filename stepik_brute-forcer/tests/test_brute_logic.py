"""
Тесты для модуля brute_logic.py
"""
import pytest
from modules.brute_logic import BruteForceLogic
from modules.number_generator import NumberGenerator


class TestBruteLogic:
    """Тесты логики перебора"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.generator = NumberGenerator()

    def test_number_generator_range(self):
        """Тест генерации числового диапазона"""
        # Целые числа
        result = self.generator.generate_range(1, 5, 1, 0)
        assert result == ['1', '2', '3', '4', '5']

        # Дробные числа
        result = self.generator.generate_range(0, 1, 0.5, 1)
        assert result == ['0', '0.5', '1']

        # Отрицательный шаг
        result = self.generator.generate_range(5, 1, -1, 0)
        assert result == ['5', '4', '3', '2', '1']

    def test_number_generator_precision(self):
        """Тест точности чисел"""
        result = self.generator.generate_range(0.123, 0.126, 0.001, 3)
        assert '0.123' in result
        assert '0.124' in result
        assert '0.125' in result

    def test_format_number(self):
        """Тест форматирования чисел"""
        from decimal import Decimal

        # Целое число
        result = self.generator.format_number(Decimal('5'), 0)
        assert result == '5'

        # Дробное число с округлением
        result = self.generator.format_number(Decimal('3.14159'), 2)
        assert result == '3.14'

        # Удаление лишних нулей
        result = self.generator.format_number(Decimal('2.500'), 2)
        assert result == '2.5'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])