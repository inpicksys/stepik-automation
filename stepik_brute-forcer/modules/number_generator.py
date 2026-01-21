"""
Генератор числовых последовательностей
"""
from decimal import Decimal, ROUND_HALF_UP
import numpy as np


class NumberGenerator:
    def __init__(self):
        pass

    def generate_range(self, start, end, step, precision=0):
        """
        Генерация последовательности чисел

        Args:
            start: начальное значение
            end: конечное значение
            step: шаг
            precision: точность (количество знаков после запятой)

        Returns:
            list: список чисел в виде строк
        """
        if step == 0:
            raise ValueError("Шаг не может быть равен 0")

        numbers = []

        # Используем Decimal для точности
        current = Decimal(str(start))
        step_dec = Decimal(str(step))
        end_dec = Decimal(str(end))

        # Определяем направление
        if step > 0:
            while current <= end_dec:
                numbers.append(self.format_number(current, precision))
                current += step_dec
        else:
            while current >= end_dec:
                numbers.append(self.format_number(current, precision))
                current += step_dec

        return numbers

    def format_number(self, number, precision=0):
        """
        Форматирование числа

        Args:
            number: Decimal число
            precision: точность

        Returns:
            str: отформатированное число
        """
        # Округление
        if precision > 0:
            number = number.quantize(
                Decimal('1.' + '0' * precision),
                rounding=ROUND_HALF_UP
            )
        else:
            number = number.to_integral_value(rounding=ROUND_HALF_UP)

        # Преобразование в строку
        result = str(number)

        # Удаление лишних нулей
        if '.' in result:
            result = result.rstrip('0').rstrip('.')

        return result

    def generate_exponential(self, start, end, base=10, count=100):
        """Генерация экспоненциальной последовательности"""
        return np.logspace(np.log10(start), np.log10(end), count, base=base)

    def generate_geometric(self, start, ratio, count=100):
        """Генерация геометрической прогрессии"""
        return [start * (ratio ** i) for i in range(count)]