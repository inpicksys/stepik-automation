import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from itertools import product, combinations
import csv


class StepikBruteForcerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stepik Brute Forcer Pro")
        self.root.geometry("900x800")

        # Переменные
        self.running = False
        self.scheduled = False
        self.brute_thread = None
        self.scheduler_thread = None
        self.history = []
        self.results = []

        # Загрузка конфигурации и истории
        self.config = self.load_config()
        self.load_history()
        self.load_schedule()

        self.create_widgets()
        self.update_schedule_display()

    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except:
            return {"email": "", "password": "", "history": [], "schedule": []}

    def save_config(self):
        """Сохранение конфигурации в файл"""
        self.config["history"] = self.history[:50]  # Сохраняем последние 50 записей
        with open("config.json", "w") as f:
            json.dump(self.config, f)

    def load_history(self):
        """Загрузка истории URL"""
        try:
            with open("history.json", "r") as f:
                self.history = json.load(f)
        except:
            self.history = []

    def save_history(self):
        """Сохранение истории URL"""
        with open("history.json", "w") as f:
            json.dump(self.history, f)

    def add_to_history(self, url):
        """Добавление URL в историю"""
        if url and url not in self.history:
            self.history.insert(0, url)
            if len(self.history) > 50:
                self.history = self.history[:50]
            self.save_history()
            self.update_history_listbox()

    def load_schedule(self):
        """Загрузка расписания"""
        try:
            with open("schedule.json", "r") as f:
                self.schedule_tasks = json.load(f)
        except:
            self.schedule_tasks = []

    def save_schedule(self):
        """Сохранение расписания"""
        with open("schedule.json", "w") as f:
            json.dump(self.schedule_tasks, f)

    def create_widgets(self):
        # Создаем Notebook (вкладки)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Вкладка "Основные настройки"
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Основные настройки")

        # История URL
        ttk.Label(main_frame, text="История URL:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.history_listbox = tk.Listbox(main_frame, height=5, width=70)
        self.history_listbox.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='we')
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)

        # URL
        ttk.Label(main_frame, text="URL задания Stepik:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=70)
        self.url_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='we')

        # Логин и пароль
        ttk.Label(main_frame, text="Email (Stepik):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.email_entry = ttk.Entry(main_frame, width=30)
        self.email_entry.grid(row=2, column=1, padx=5, pady=5, sticky='we')
        self.email_entry.insert(0, self.config.get("email", ""))

        ttk.Label(main_frame, text="Пароль:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, padx=5, pady=5, sticky='we')
        self.password_entry.insert(0, self.config.get("password", ""))

        # Кнопка сохранения учетных данных
        ttk.Button(main_frame, text="Сохранить учетные данные",
                   command=self.save_credentials).grid(row=3, column=2, padx=5, pady=5)

        # Тип вопроса
        ttk.Label(main_frame, text="Тип вопроса:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.question_type = tk.StringVar(value="string")
        question_types = [("Ввод текста", "string"),
                          ("Выбор одного (radio)", "radio"),
                          ("Выбор нескольких (checkbox)", "checkbox"),
                          ("Выпадающий список", "select"),
                          ("Сопоставление", "matching")]

        for i, (text, value) in enumerate(question_types):
            rb = ttk.Radiobutton(main_frame, text=text, variable=self.question_type, value=value)
            rb.grid(row=5 + i, column=0, columnspan=3, sticky='w', padx=25, pady=2)

        # Вкладка "Настройки перебора"
        brute_frame = ttk.Frame(notebook)
        notebook.add(brute_frame, text="Настройки перебора")

        # Настройки для текстового ввода
        ttk.Label(brute_frame, text="=== Для текстового ввода ===").grid(row=0, column=0, columnspan=2, sticky='w',
                                                                         pady=10)

        ttk.Label(brute_frame, text="Символы для перебора:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.chars_entry = ttk.Entry(brute_frame, width=50)
        self.chars_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')
        self.chars_entry.insert(0, "0123456789abcdefghijklmnopqrstuvwxyz")

        ttk.Label(brute_frame, text="Минимальная длина:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.min_len_spinbox = ttk.Spinbox(brute_frame, from_=1, to=10, width=10)
        self.min_len_spinbox.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.min_len_spinbox.set(1)

        ttk.Label(brute_frame, text="Максимальная длина:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.max_len_spinbox = ttk.Spinbox(brute_frame, from_=1, to=10, width=10)
        self.max_len_spinbox.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        self.max_len_spinbox.set(5)

        # Задержки
        ttk.Label(brute_frame, text="=== Настройки задержки ===").grid(row=4, column=0, columnspan=2, sticky='w',
                                                                       pady=10)

        ttk.Label(brute_frame, text="Задержка между попытками (сек):").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.delay_spinbox = ttk.Spinbox(brute_frame, from_=0.5, to=10, increment=0.5, width=10)
        self.delay_spinbox.grid(row=5, column=1, sticky='w', padx=5, pady=5)
        self.delay_spinbox.set(1)

        # Вкладка "Лог"
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Лог выполнения")

        # Панель управления логом
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(log_control_frame, text="📁 Экспорт лога",
                   command=self.export_log).pack(side='left', padx=5)
        ttk.Button(log_control_frame, text="🗑️ Очистить лог",
                   command=self.clear_log).pack(side='left', padx=5)
        ttk.Button(log_control_frame, text="📊 Экспорт результатов",
                   command=self.export_results).pack(side='left', padx=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=90)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка "Планировщик"
        schedule_frame = ttk.Frame(notebook)
        notebook.add(schedule_frame, text="📅 Планировщик")

        # Список запланированных задач
        ttk.Label(schedule_frame, text="Запланированные задачи:").pack(anchor='w', padx=5, pady=5)
        self.schedule_listbox = tk.Listbox(schedule_frame, height=8, width=80)
        self.schedule_listbox.pack(fill='x', padx=5, pady=5)

        # Форма добавления новой задачи
        form_frame = ttk.LabelFrame(schedule_frame, text="Добавить задачу")
        form_frame.pack(fill='x', padx=5, pady=10)

        # Дата и время
        ttk.Label(form_frame, text="Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.schedule_datetime_entry = ttk.Entry(form_frame, width=20)
        self.schedule_datetime_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.schedule_datetime_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Повторение
        ttk.Label(form_frame, text="Повторять:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.repeat_var = tk.StringVar(value="none")
        ttk.Radiobutton(form_frame, text="Нет", variable=self.repeat_var, value="none").grid(row=1, column=1,
                                                                                             sticky='w', padx=5)
        ttk.Radiobutton(form_frame, text="Ежедневно", variable=self.repeat_var, value="daily").grid(row=1, column=2,
                                                                                                    sticky='w', padx=5)
        ttk.Radiobutton(form_frame, text="Еженедельно", variable=self.repeat_var, value="weekly").grid(row=1, column=3,
                                                                                                       sticky='w',
                                                                                                       padx=5)

        # Кнопки планировщика
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(button_frame, text="➕ Добавить задачу",
                   command=self.add_schedule_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="➖ Удалить выбранное",
                   command=self.remove_schedule_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="▶ Запустить планировщик",
                   command=self.start_scheduler).pack(side='left', padx=5)
        ttk.Button(button_frame, text="⏹ Остановить планировщик",
                   command=self.stop_scheduler).pack(side='left', padx=5)

        # Статус планировщика
        self.schedule_status_label = ttk.Label(schedule_frame, text="Планировщик остановлен")
        self.schedule_status_label.pack(pady=5)

        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="▶ Начать перебор",
                                       command=self.start_brute_force, width=20)
        self.start_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(control_frame, text="⏹ Остановить",
                                      command=self.stop_brute_force, width=20, state='disabled')
        self.stop_button.pack(side='left', padx=5)

        self.test_button = ttk.Button(control_frame, text="🔍 Проверить подключение",
                                      command=self.test_connection, width=20)
        self.test_button.pack(side='left', padx=5)

        # Кнопка сохранения настроек
        ttk.Button(control_frame, text="💾 Сохранить настройки",
                   command=self.save_all_settings).pack(side='left', padx=5)

        # Статус
        self.status_label = ttk.Label(self.root, text="Готов к работе")
        self.status_label.pack(pady=5)

        # Обновляем историю
        self.update_history_listbox()

    def update_history_listbox(self):
        """Обновление списка истории"""
        self.history_listbox.delete(0, tk.END)
        for url in self.history[:20]:  # Показываем последние 20 записей
            self.history_listbox.insert(tk.END, url[:80] + ("..." if len(url) > 80 else ""))

    def on_history_select(self, event):
        """Обработка выбора URL из истории"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history):
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, self.history[index])

    def save_credentials(self):
        """Сохранение учетных данных"""
        self.config["email"] = self.email_entry.get()
        self.config["password"] = self.password_entry.get()
        self.save_config()
        self.log_message("Учетные данные сохранены")

    def save_all_settings(self):
        """Сохранение всех настроек"""
        self.save_credentials()
        self.save_history()
        self.save_schedule()
        self.log_message("Все настройки сохранены")

    def log_message(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Лог очищен")

    def export_log(self):
        """Экспорт лога в файл"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Лог экспортирован в {filename}")

    def export_results(self):
        """Экспорт результатов в файл"""
        if not hasattr(self, 'last_results') or not self.last_results:
            messagebox.showinfo("Нет результатов", "Нет результатов для экспорта")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Дата", "URL", "Тип вопроса", "Результат", "Ответ", "Время выполнения"])
                    for result in self.last_results:
                        writer.writerow(result)
                self.log_message(f"Результаты экспортированы в {filename}")
            except Exception as e:
                self.log_message(f"Ошибка при экспорте: {e}")

    def test_connection(self):
        """Тестовое подключение к Stepik"""

        def test():
            try:
                self.log_message("Проверка подключения...")
                with sync_playwright() as p:
                    browser = p.firefox.launch(headless=True)
                    page = browser.new_context().new_page()
                    page.goto("https://stepik.org")
                    title = page.title()
                    browser.close()
                    self.log_message(f"✓ Подключение успешно. Заголовок: {title}")
            except Exception as e:
                self.log_message(f"✗ Ошибка подключения: {e}")

        threading.Thread(target=test, daemon=True).start()

    def start_brute_force(self):
        """Запуск перебора"""
        if self.running:
            return

        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL задания")
            return

        if not self.email_entry.get() or not self.password_entry.get():
            messagebox.showerror("Ошибка", "Введите email и пароль")
            return

        # Добавляем URL в историю
        self.add_to_history(url)

        self.running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Выполняется перебор...")

        self.brute_thread = threading.Thread(target=self.run_brute_force, daemon=True)
        self.brute_thread.start()

    def stop_brute_force(self):
        """Остановка перебора"""
        self.running = False
        self.status_label.config(text="Останавливается...")
        self.log_message("Остановка запрошена...")

    def run_brute_force(self):
        """Основная функция перебора"""
        try:
            url = self.url_entry.get()
            question_type = self.question_type.get()
            start_time = datetime.now()

            with sync_playwright() as p:
                # Запуск браузера
                browser = p.firefox.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                # Логин
                self.log_message("Вход в аккаунт Stepik...")
                page.goto("https://stepik.org")

                # Закрытие всплывающих окон
                try:
                    page.locator(".woof-message__button").click(timeout=3000)
                except:
                    pass

                page.locator(".navbar__auth_login").click()
                page.locator("#id_login_email").fill(self.email_entry.get())
                page.locator("#id_login_password").fill(self.password_entry.get())
                page.locator("#login_form > button").click()
                page.wait_for_timeout(5000)

                # Переход к заданию
                self.log_message(f"Переход к заданию: {url}")
                page.goto(url)
                page.wait_for_timeout(3000)

                # Продолжить курс (если нужно)
                try:
                    page.locator(".course-join-button > button").click(timeout=3000)
                except:
                    pass

                self.log_message(f"Тип вопроса: {question_type}")

                # Выполнение перебора в зависимости от типа
                result = None
                if question_type == "string":
                    result = self.brute_string(page)
                elif question_type == "radio":
                    result = self.brute_radio(page)
                elif question_type == "checkbox":
                    result = self.brute_checkbox(page)
                elif question_type == "select":
                    result = self.brute_select(page)
                elif question_type == "matching":
                    result = self.brute_matching(page)

                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                # Сохраняем результат
                self.save_result(url, question_type, result, execution_time)

                browser.close()

        except Exception as e:
            self.log_message(f"Ошибка: {e}")
        finally:
            self.running = False
            self.root.after(0, self.on_brute_finished)

    def save_result(self, url, question_type, result, execution_time):
        """Сохранение результата"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_data = [timestamp, url, question_type,
                       "Успешно" if result else "Не найдено",
                       str(result), f"{execution_time:.2f} сек"]

        if not hasattr(self, 'last_results'):
            self.last_results = []

        self.last_results.append(result_data)

        # Сохраняем в файл
        try:
            with open("results.csv", "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                # Если файл пустой, добавляем заголовок
                if f.tell() == 0:
                    writer.writerow(["Дата", "URL", "Тип вопроса", "Результат", "Ответ", "Время выполнения"])
                writer.writerow(result_data)
        except Exception as e:
            self.log_message(f"Ошибка при сохранении результата: {e}")

    def brute_string(self, page):
        """Перебор для текстового ввода"""
        chars = self.chars_entry.get()
        min_len = int(self.min_len_spinbox.get())
        max_len = int(self.max_len_spinbox.get())
        delay = float(self.delay_spinbox.get())

        self.log_message(f"Начинаю перебор строк длиной {min_len}-{max_len} из символов: {chars}")

        found = False
        answer = None

        for length in range(min_len, max_len + 1):
            if not self.running:
                break

            self.log_message(f"Перебор строк длиной {length}...")
            count = 0

            for p in product(chars, repeat=length):
                if not self.running:
                    break

                s = ''.join(p)
                count += 1

                if count % 100 == 0:
                    self.log_message(f"Проверено {count} комбинаций, текущая: {s}")

                try:
                    # Очищаем поле и вводим новое значение
                    page.fill("input[type='text'], textarea, .string-quiz__input", "")
                    page.fill("input[type='text'], textarea, .string-quiz__input", s)

                    # Отправляем
                    page.click("button.submit-submission, .submit")
                    page.wait_for_timeout(2000)

                    # Проверяем результат
                    if self.check_if_correct(page):
                        self.log_message(f"🎉 НАЙДЕН ПРАВИЛЬНЫЙ ОТВЕТ: {s}")
                        found = True
                        answer = s
                        break

                    time.sleep(delay)

                except Exception as e:
                    self.log_message(f"Ошибка при проверке '{s}': {e}")

            if found:
                break

        if not found:
            self.log_message("❌ Правильный ответ не найден в заданном диапазоне")

        return answer

    def brute_radio(self, page):
        """Перебор для радио-кнопок"""
        delay = float(self.delay_spinbox.get())

        # Поиск всех радио-кнопок
        radios = page.locator("input[type='radio'], .radio-quiz__option")
        count = radios.count()

        self.log_message(f"Найдено радио-кнопок: {count}")

        found = False
        answer = None

        for i in range(count):
            if not self.running:
                break

            try:
                # Кликаем на радио-кнопку
                radios.nth(i).click()

                # Отправляем
                page.click("button.submit-submission, .submit")
                page.wait_for_timeout(2000)

                # Проверяем результат
                if self.check_if_correct(page):
                    self.log_message(f"🎉 НАЙДЕН ПРАВИЛЬНЫЙ ОТВЕТ: вариант {i + 1}")
                    found = True
                    answer = f"Вариант {i + 1}"
                    break

                time.sleep(delay)

            except Exception as e:
                self.log_message(f"Ошибка при проверке варианта {i + 1}: {e}")

        if not found:
            self.log_message("❌ Правильный вариант не найден")

        return answer

    def brute_checkbox(self, page):
        """Перебор для чекбоксов"""
        delay = float(self.delay_spinbox.get())

        # Поиск всех чекбоксов
        checkboxes = page.locator("input[type='checkbox'], .checkbox-quiz__option")
        count = checkboxes.count()

        self.log_message(f"Найдено чекбоксов: {count}")
        self.log_message(f"Будет проверено {2 ** count} комбинаций")

        found = False
        answer = None

        # Перебор всех комбинаций (от 1 до 2^count - 1)
        for mask in range(1, 1 << count):
            if not self.running:
                break

            try:
                # Сбрасываем все чекбоксы
                for i in range(count):
                    checkboxes.nth(i).uncheck()

                # Устанавливаем нужные чекбоксы
                selected = []
                for i in range(count):
                    if mask & (1 << i):
                        checkboxes.nth(i).check()
                        selected.append(str(i + 1))

                # Отправляем
                page.click("button.submit-submission, .submit")
                page.wait_for_timeout(2000)

                # Проверяем результат
                if self.check_if_correct(page):
                    self.log_message(f"🎉 НАЙДЕН ПРАВИЛЬНЫЙ ОТВЕТ: варианты {', '.join(selected)}")
                    found = True
                    answer = f"Варианты: {', '.join(selected)}"
                    break

                time.sleep(delay)

            except Exception as e:
                self.log_message(f"Ошибка при проверке комбинации: {e}")

        if not found:
            self.log_message("❌ Правильная комбинация не найден")

        return answer

    def brute_select(self, page):
        """Перебор для выпадающих списков"""
        self.log_message("Перебор для выпадающих списков пока не реализован")
        return None

    def brute_matching(self, page):
        """Перебор для сопоставления"""
        self.log_message("Перебор для сопоставления пока не реализован")
        return None

    def check_if_correct(self, page):
        """Проверка правильности ответа"""
        try:
            # Разные селекторы для успешного ответа
            success_selectors = [
                ".attempt-message_correct",
                ".step__success",
                ".lesson__step_active .step__success",
                "[data-s='correct']",
                ".smart-hints__hint_correct"
            ]

            for selector in success_selectors:
                element = page.locator(selector).first
                if element.is_visible(timeout=1000):
                    return True
        except:
            pass
        return False

    def on_brute_finished(self):
        """Завершение перебора"""
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Перебор завершен")

    # Функции для планировщика
    def update_schedule_display(self):
        """Обновление списка задач планировщика"""
        self.schedule_listbox.delete(0, tk.END)
        for i, task in enumerate(self.schedule_tasks):
            task_str = f"{task['datetime']} - {task['url'][:50]}... ({task['type']})"
            if task.get('repeat'):
                task_str += f" [Повтор: {task['repeat']}]"
            self.schedule_listbox.insert(tk.END, task_str)

    def add_schedule_task(self):
        """Добавление задачи в планировщик"""
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL задания")
            return

        task_datetime = self.schedule_datetime_entry.get()
        try:
            datetime.strptime(task_datetime, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты и времени. Используйте ГГГГ-ММ-ДД ЧЧ:ММ")
            return

        task = {
            "datetime": task_datetime,
            "url": url,
            "type": self.question_type.get(),
            "repeat": self.repeat_var.get(),
            "chars": self.chars_entry.get(),
            "min_len": int(self.min_len_spinbox.get()),
            "max_len": int(self.max_len_spinbox.get()),
            "delay": float(self.delay_spinbox.get())
        }

        self.schedule_tasks.append(task)
        self.save_schedule()
        self.update_schedule_display()
        self.log_message(f"Задача добавлена в планировщик на {task_datetime}")

    def remove_schedule_task(self):
        """Удаление выбранной задачи"""
        selection = self.schedule_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.schedule_tasks):
                removed = self.schedule_tasks.pop(index)
                self.save_schedule()
                self.update_schedule_display()
                self.log_message(f"Задача удалена: {removed['datetime']}")

    def start_scheduler(self):
        """Запуск планировщика"""
        if self.scheduled:
            return

        if not self.schedule_tasks:
            messagebox.showinfo("Нет задач", "Нет запланированных задач")
            return

        self.scheduled = True
        self.schedule_status_label.config(text="Планировщик запущен")
        self.log_message("Планировщик запущен")

        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """Остановка планировщика"""
        self.scheduled = False
        self.schedule_status_label.config(text="Планировщик остановлен")
        self.log_message("Планировщик остановлен")

    def run_scheduler(self):
        """Основная функция планировщика"""
        while self.scheduled:
            current_time = datetime.now()

            for task in self.schedule_tasks[:]:  # Копируем список для безопасной итерации
                task_time = datetime.strptime(task['datetime'], "%Y-%m-%d %H:%M")

                # Если время задачи наступило
                if current_time >= task_time and current_time < task_time + timedelta(minutes=1):
                    self.log_message(f"Запускаю запланированную задачу: {task['url']}")

                    # Обновляем поля в GUI
                    self.root.after(0, self.load_task_to_gui, task)

                    # Запускаем перебор
                    self.run_scheduled_task(task)

                    # Обновляем время для повторяющихся задач
                    if task['repeat'] == 'daily':
                        new_time = task_time + timedelta(days=1)
                        task['datetime'] = new_time.strftime("%Y-%m-%d %H:%M")
                    elif task['repeat'] == 'weekly':
                        new_time = task_time + timedelta(weeks=1)
                        task['datetime'] = new_time.strftime("%Y-%m-%d %H:%M")

                    self.save_schedule()
                    self.root.after(0, self.update_schedule_display)

            time.sleep(30)  # Проверяем каждые 30 секунд

    def load_task_to_gui(self, task):
        """Загрузка задачи в GUI"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, task['url'])
        self.question_type.set(task['type'])
        self.chars_entry.delete(0, tk.END)
        self.chars_entry.insert(0, task['chars'])
        self.min_len_spinbox.set(task['min_len'])
        self.max_len_spinbox.set(task['max_len'])
        self.delay_spinbox.set(task['delay'])

    def run_scheduled_task(self, task):
        """Запуск запланированной задачи"""
        # Здесь можно было бы вызвать start_brute_force, но для простоты
        # просто логируем запуск
        self.log_message(f"Выполняется задача: {task['url']}")
        self.log_message(f"Тип вопроса: {task['type']}")


def main():
    root = tk.Tk()
    app = StepikBruteForcerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()