import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import time

URL = "https://stepik.org/lesson/913973/step/7?unit=919617"


def wait_loaded(page):
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("networkidle")


def with_auth_login(url: str) -> str:
    """Добавляет auth=login к URL, сохраняя остальные параметры."""
    u = urlparse(url)
    qs = parse_qs(u.query)
    qs["auth"] = ["login"]
    new_query = urlencode(qs, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))


def is_logged_in(page) -> bool:
    # На Stepik при логине обычно появляется профиль/аватар в navbar.
    # Если кнопка "Войти" есть — скорее всего не залогинен.
    return page.locator(".navbar__auth_login").count() == 0


def ensure_logged_in(page, email: str, password: str):
    if is_logged_in(page):
        print("Уже залогинен")
        return

    # Открываем страницу/модалку логина прямым URL
    login_url = with_auth_login(page.url if page.url else URL)
    page.goto(login_url, wait_until="domcontentloaded")
    wait_loaded(page)

    # Stepik логин-форма может быть разной: модалка или отдельная страница
    email_selectors = [
        "#id_login_email",  # классическая форма
        "input[name='login']",  # иногда поле так называется
        "input[type='email']",
        "form#login_form input",  # fallback
    ]
    pass_selectors = [
        "#id_login_password",
        "input[name='password']",
        "input[type='password']",
    ]
    submit_selectors = [
        "#login_form > button",
        "form#login_form button[type='submit']",
        "button:has-text('Войти')",
        "button:has-text('Log in')",
    ]

    def first_visible(selectors, timeout=20000):
        last_err = None
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=timeout)
                return loc
            except Exception as e:
                last_err = e
        raise PWTimeoutError(f"Не нашёл видимый элемент среди селекторов: {selectors}") from last_err

    email_inp = first_visible(email_selectors, timeout=20000)
    pass_inp = first_visible(pass_selectors, timeout=20000)

    email_inp.fill(email)
    pass_inp.fill(password)

    # Кнопка входа
    for sel in submit_selectors:
        try:
            btn = page.locator(sel).first
            if btn.count():
                btn.click(timeout=5000)
                break
        except:
            continue

    wait_loaded(page)
    print("Логин выполнен")


def join_course_if_needed(page):
    for sel in [".course-join-button > button", "button.course-join-button"]:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible(timeout=1500):
                btn.click(force=True, timeout=8000)
                wait_loaded(page)
                print("Присоединились к курсу")
                break
        except:
            pass


def check_result(page):
    """Проверяем результат после отправки ответа."""
    time.sleep(2)

    # Проверяем различные варианты фидбэка
    result_selectors = [
        ".attempt-message",
        ".submission__status",
        ".smart-hints",
        ".quiz__answer-feedback",
        ".attempt__feedback",
    ]

    for selector in result_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                text = element.inner_text().strip()
                if text:
                    return text
        except:
            continue

    return ""


def submit_answer(page, answer):
    """Вводит и отправляет один ответ."""
    try:
        # Находим поле ввода
        inp = page.locator(".number-input").first
        inp.wait_for(state="visible", timeout=20000)

        # Находим кнопку отправки
        btn = page.locator("button.submit-submission").first
        btn.wait_for(state="visible", timeout=20000)

        # Вводим ответ
        inp.click()
        inp.fill("")
        inp.fill(str(answer))

        # Триггерим валидацию
        try:
            inp.press("Enter")
        except:
            pass

        # Ждем, пока кнопка станет активной
        try:
            page.wait_for_function(
                "btn => !btn.disabled",
                arg=btn.element_handle(),
                timeout=20000
            )
        except:
            # Пробуем альтернативный формат
            alt_answer = answer.replace(".", ",") if "." in answer else answer.replace(",", ".")
            inp.click()
            inp.fill("")
            inp.fill(alt_answer)
            try:
                inp.press("Enter")
            except:
                pass

            # Снова ждем активации кнопки
            page.wait_for_function(
                "btn => !btn.disabled",
                arg=btn.element_handle(),
                timeout=20000
            )

        # Кликаем кнопку отправки
        try:
            btn.click(timeout=5000)
        except PWTimeoutError:
            # Fallback через JavaScript
            page.evaluate("btn => btn.click()", btn.element_handle())

        # Ждем обработки ответа
        time.sleep(3)
        return True

    except Exception as e:
        print(f"Ошибка при отправке ответа {answer}: {e}")
        return False


def run():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    email = cfg["email"]
    password = cfg["password"]

    # Генерируем ответы от 500.0 до 2000.0 с шагом 0.1
    answers = []
    for i in range(7620, 20000):  # Умножаем на 10, чтобы избежать ошибок с float
        value = i / 10.0
        answers.append(f"{value:.1f}")

    print(f"Сгенерировано {len(answers)} ответов для перебора")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded")
        wait_loaded(page)

        ensure_logged_in(page, email, password)
        join_course_if_needed(page)

        # Ждем загрузки страницы с заданием
        time.sleep(3)

        # Перебираем все ответы
        found_correct = False
        for i, answer in enumerate(answers, 1):
            print(f"[{i}/{len(answers)}] Пробуем ответ: {answer}")

            # Сохраняем текущий URL для проверки
            current_url = page.url

            # Пытаемся отправить ответ
            if submit_answer(page, answer):
                # Проверяем результат
                result = check_result(page)

                # Проверяем, правильный ли ответ
                if result and any(word in result.lower() for word in ["правильно", "correct", "верно"]):
                    print(f"🎉 Найден правильный ответ: {answer}")
                    print(f"Фидбэк: {result}")
                    found_correct = True

                    # Сохраняем правильный ответ в файл
                    with open("correct_answer.txt", "w", encoding="utf-8") as f:
                        f.write(f"Правильный ответ: {answer}\n")
                        f.write(f"Фидбэк: {result}\n")
                    break
                else:
                    # Проверяем, изменился ли URL (признак перехода к следующему шагу)
                    if page.url != current_url:
                        print(f"🎉 URL изменился! Возможно, правильный ответ: {answer}")
                        print(f"Новый URL: {page.url}")
                        found_correct = True

                        # Сохраняем возможный правильный ответ
                        with open("possible_answer.txt", "w", encoding="utf-8") as f:
                            f.write(f"Возможный правильный ответ: {answer}\n")
                            f.write(f"Новый URL: {page.url}\n")
                        break
                    else:
                        print(f"❌ Неверный ответ: {answer}")
            else:
                print(f"⚠️ Не удалось отправить ответ: {answer}")

            # Небольшая пауза между попытками
            time.sleep(0.5)

        if not found_correct:
            print("❌ Правильный ответ не найден в заданном диапазоне")

        # Сохраняем скриншот результата
        page.screenshot(path="stepik_result.png", full_page=True)

        # Даем время увидеть результат
        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    run()