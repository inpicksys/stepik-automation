"""
API для работы с Stepik
"""
from playwright.sync_api import sync_playwright
import threading


class StepikAPI:
    def __init__(self, app):
        self.app = app

    def test_connection(self):
        """Тестирование подключения к Stepik"""

        def test():
            self.app.log_message("🔍 Тестирую подключение к Stepik...")
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    )
                    page = context.new_page()

                    # Переходим на главную страницу
                    page.goto("https://stepik.org", wait_until="networkidle", timeout=15000)

                    # Проверяем заголовок
                    title = page.title()
                    if "Stepik" in title:
                        self.app.log_message(f"✅ Подключение успешно! Заголовок: {title}")

                        # Пробуем найти элементы входа
                        login_buttons = page.locator("text=Войти").count()
                        if login_buttons > 0:
                            self.app.log_message("✅ Форма входа доступна")
                        else:
                            self.app.log_message("⚠️ Форма входа не найдена")
                    else:
                        self.app.log_message("❌ Не удалось загрузить Stepik")

                    browser.close()

            except Exception as e:
                self.app.log_message(f"❌ Ошибка подключения: {str(e)[:100]}")

        # Запускаем в отдельном потоке
        threading.Thread(target=test, daemon=True).start()

    def login(self, email, password, page):
        """Авторизация на Stepik"""
        try:
            self.app.log_message("Вход в аккаунт...")

            # Переход на страницу входа
            page.goto("https://stepik.org/login", wait_until="networkidle")

            # Закрываем возможные всплывающие окна
            try:
                page.locator("button:has-text('Принять')").click(timeout=3000)
            except:
                pass

            # Заполняем форму
            page.fill("input[name='login']", email)
            page.fill("input[name='password']", password)

            # Отправляем форму
            page.click("button[type='submit']")

            # Ждем загрузки
            page.wait_for_timeout(5000)

            # Проверяем успешность входа
            if page.locator("a[href^='/users/']").count() > 0:
                self.app.log_message("✅ Успешный вход в аккаунт")
                return True
            else:
                # Проверяем наличие ошибок
                error_elements = page.locator(".alert-danger, .error, .has-error").count()
                if error_elements > 0:
                    self.app.log_message("❌ Ошибка входа: неверные данные")
                else:
                    self.app.log_message("❌ Неизвестная ошибка входа")
                return False

        except Exception as e:
            self.app.log_message(f"❌ Ошибка при входе: {str(e)[:100]}")
            return False

    def submit_answer(self, page, answer, question_type):
        """Отправка ответа на Stepik"""
        try:
            # В зависимости от типа вопроса
            if question_type == "string":
                input_field = page.locator("input[type='text'], textarea").first
                input_field.fill(str(answer))
            elif question_type == "number":
                input_field = page.locator("input[type='text'], textarea").first
                input_field.fill(str(answer))
            elif question_type == "radio":
                # Кликаем на радиокнопку с нужным значением
                page.locator(f"input[type='radio'][value='{answer}']").click()
            elif question_type == "checkbox":
                # Для чекбоксов answer может быть списком
                pass

            # Нажимаем кнопку отправки
            submit_buttons = [
                "button:has-text('Отправить')",
                "button:has-text('Submit')",
                "button.submit-submission",
                "button[type='submit']"
            ]

            for button in submit_buttons:
                if page.locator(button).count() > 0:
                    page.locator(button).first.click()
                    break

            page.wait_for_timeout(2000)
            return True

        except Exception as e:
            self.app.log_message(f"Ошибка отправки ответа: {e}")
            return False