"""
Логика перебора
"""
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from itertools import product
from .number_generator import NumberGenerator


class BruteForceLogic:
    def __init__(self, app):
        self.app = app
        self.number_gen = NumberGenerator()

    def brute_number(self, url, email, password, start, end, step, precision, delay):
        """Числовой перебор"""
        try:
            self.app.log_message(f"🔢 Начинаю числовой перебор от {start} до {end} шаг {step}")

            # Генерация чисел
            numbers = self.number_gen.generate_range(start, end, step, precision)
            self.app.log_message(f"Сгенерировано {len(numbers):,} чисел")

            # Используем удаленный или локальный браузер
            if self.app.config.get("use_remote", False):
                browser = self.app.remote_playwright.connect()
                if not browser:
                    self.app.log_message("Использую локальный браузер")
                    browser = self._launch_local_browser()
            else:
                browser = self._launch_local_browser()

            with browser:
                context = browser.new_context()
                page = context.new_page()

                # Логин
                if not self._login(page, email, password):
                    return None

                # Переход к заданию
                page.goto(url)
                page.wait_for_timeout(3000)

                # Поиск поля ввода
                input_field = self._find_input_field(page)
                if not input_field:
                    self.app.log_message("Не найдено поле ввода")
                    return None

                # Перебор чисел
                found = False
                answer = None

                for i, number in enumerate(numbers):
                    if not self.app.running:
                        break

                    # Обновление прогресса
                    progress = (i + 1) / len(numbers) * 100
                    self.app.progress_var.set(progress)

                    if i % 100 == 0:
                        self.app.log_message(f"Проверено {i:,}/{len(numbers):,} ({progress:.1f}%)")

                    # Ввод числа
                    input_field.fill("")
                    input_field.fill(str(number))

                    # Отправка
                    if self._submit_answer(page):
                        if self._check_answer(page):
                            self.app.log_message(f"🎉 Найден ответ: {number}")
                            found = True
                            answer = number
                            break

                    time.sleep(delay)

                # Возврат результата
                if found:
                    return [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        url,
                        "number",
                        "Успешно",
                        str(answer),
                        f"{i + 1} попыток"
                    ]
                else:
                    self.app.log_message("❌ Ответ не найден")
                    return None

        except Exception as e:
            self.app.log_message(f"Ошибка при переборе: {e}")
            return None

    def brute_string(self, url, email, password, chars, min_len, max_len, delay):
        """Строковый перебор"""
        # Реализация строкового перебора
        pass

    def brute_other(self, url, email, password, qtype, delay):
        """Перебор для других типов вопросов"""
        # Реализация для radio, checkbox и т.д.
        pass

    def _launch_local_browser(self):
        """Запуск локального браузера"""
        with sync_playwright() as p:
            return p.chromium.launch(headless=False)

    def _login(self, page, email, password):
        """Авторизация на Stepik"""
        try:
            page.goto("https://stepik.org")
            page.wait_for_timeout(2000)

            # Закрытие cookie
            try:
                page.click("text=Принять", timeout=2000)
            except:
                pass

            # Клик на вход
            page.click("text=Войти")
            page.wait_for_timeout(2000)

            # Заполнение формы
            page.fill("input[name='login']", email)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            page.wait_for_timeout(5000)

            # Проверка успешности
            if page.locator("text=Мой профиль").count() > 0:
                self.app.log_message("✓ Успешный вход")
                return True
            else:
                self.app.log_message("❌ Ошибка входа")
                return False

        except Exception as e:
            self.app.log_message(f"Ошибка при входе: {e}")
            return False

    def _find_input_field(self, page):
        """Поиск поля ввода"""
        selectors = [
            "input[type='text']",
            "textarea",
            ".text-area",
            ".string-quiz__input",
            "[contenteditable='true']"
        ]

        for selector in selectors:
            if page.locator(selector).count() > 0:
                return page.locator(selector).first

        return None

    def _submit_answer(self, page):
        """Отправка ответа"""
        try:
            buttons = [
                "button.submit-submission",
                "button:has-text('Отправить')",
                "button:has-text('Submit')",
                "[type='submit']"
            ]

            for button in buttons:
                if page.locator(button).count() > 0:
                    page.locator(button).first.click()
                    page.wait_for_timeout(2000)
                    return True

            return False
        except:
            return False

    def _check_answer(self, page):
        """Проверка правильности ответа"""
        success_indicators = [
            ".correct",
            ".success",
            ".attempt-message_correct",
            "text=правильно",
            "text=верно",
            "text=correct"
        ]

        for indicator in success_indicators:
            try:
                if page.locator(indicator).first.is_visible(timeout=1000):
                    return True
            except:
                continue

        return False