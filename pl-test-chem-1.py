import json
from playwright.sync_api import sync_playwright

# Загружаем логин и пароль
with open("config.json", "r") as f:
    cfg = json.load(f)

EMAIL = cfg["email"]
PASSWORD = cfg["password"]

URL = "https://stepik.org/lesson/65086/step/12?unit=41860"

from itertools import product

def permutations_with_repetition(chars, min_len, max_len):
    for length in range(min_len, max_len + 1):
        for p in product(chars, repeat=length):
            yield ''.join(p)

# пример: генерируем строки из "123" длиной 1..5
for s in permutations_with_repetition("123", 1, 5):
    print(s)


def run():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(URL)

        # --- Закрыть всплывающее окно, если есть ---
        try:
            page.locator(".woof-message__button").click(timeout=5000)
        except:
            pass

        # --- Нажать LOGIN ---
        page.locator(".navbar__auth_login").click()

        # --- Ввести email ---
        page.locator("#id_login_email").fill(EMAIL)
        # --- Ввести пароль ---
        page.locator("#id_login_password").fill(PASSWORD)

        # --- Кнопка "Войти" ---
        page.locator("#login_form > button").click()

        page.wait_for_timeout(5000)

        # --- Продолжить курс ---
        try:
            page.locator(".course-join-button > button").click(timeout=5000)
        except:
            pass

        for s in permutations_with_repetition("123", 1, 5):
            page.fill(".number-input", s)
            page.click("button.submit-submission", timeout=5000)



        # --- Готово, ты внутри урока ---
        print("Успешный вход!")

        page.wait_for_timeout(10000)
        browser.close()


if __name__ == "__main__":
    run()
