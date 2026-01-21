"""
Главный модуль GUI приложения
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime, timedelta
from modules.config_manager import ConfigManager
from modules.stepik_api import StepikAPI
from modules.brute_logic import BruteForceLogic
from modules.scheduler import TaskScheduler
from modules.remote_playwright import RemotePlaywright
from modules.number_generator import NumberGenerator
import csv
import json
import os


class StepikBruteForcerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x800")

        # Настройка шрифтов
        self.setup_fonts()

        # Инициализация менеджеров
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.stepik_api = StepikAPI(self)
        self.brute_logic = BruteForceLogic(self)
        self.scheduler = TaskScheduler(self)
        self.remote_playwright = RemotePlaywright(self)
        self.number_generator = NumberGenerator()

        # Переменные состояния
        self.running = False
        self.scheduled = False
        self.brute_thread = None
        self.scheduler_thread = None
        self.last_results = []

        # История и задачи
        self.history = self.config_manager.load_history()
        self.schedule_tasks = self.config_manager.load_schedule()

        self.create_widgets()
        self.update_schedule_display()
        self.update_history_listbox()

    def setup_fonts(self):
        """Настройка шрифтов для лучшего отображения"""
        # Используем стандартные шрифты Windows
        self.normal_font = ('Segoe UI', 10)
        self.bold_font = ('Segoe UI', 10, 'bold')
        self.title_font = ('Segoe UI', 12, 'bold')

    def create_widgets(self):
        # Notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Создание вкладок
        self.create_main_tab()
        self.create_brute_tab()
        self.create_number_tab()
        self.create_log_tab()
        self.create_scheduler_tab()
        self.create_remote_tab()

        # Панель управления
        self.create_control_panel()

    def create_main_tab(self):
        """Основные настройки"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Основные")

        # Сетка
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)

        # История URL
        ttk.Label(main_frame, text="История URL:", font=self.bold_font).grid(
            row=0, column=0, sticky='w', padx=10, pady=(10, 5))

        self.history_listbox = tk.Listbox(main_frame, height=6, width=70,
                                          font=self.normal_font,
                                          selectbackground='#0078d7', selectmode='single')
        self.history_listbox.grid(row=0, column=1, columnspan=2, padx=10, pady=(10, 5), sticky='we')
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)

        # URL задания
        ttk.Label(main_frame, text="URL задания:", font=self.bold_font).grid(
            row=1, column=0, sticky='w', padx=10, pady=5)

        self.url_entry = ttk.Entry(main_frame, width=70, font=self.normal_font)
        self.url_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky='we')

        # Email
        ttk.Label(main_frame, text="Email:", font=self.bold_font).grid(
            row=2, column=0, sticky='w', padx=10, pady=5)

        self.email_entry = ttk.Entry(main_frame, width=30, font=self.normal_font)
        self.email_entry.grid(row=2, column=1, padx=10, pady=5, sticky='we')
        self.email_entry.insert(0, self.config.get("email", ""))

        # Пароль
        ttk.Label(main_frame, text="Пароль:", font=self.bold_font).grid(
            row=3, column=0, sticky='w', padx=10, pady=5)

        self.password_entry = ttk.Entry(main_frame, width=30, font=self.normal_font, show="*")
        self.password_entry.grid(row=3, column=1, padx=10, pady=5, sticky='we')
        self.password_entry.insert(0, self.config.get("password", ""))

        # Кнопка сохранения
        ttk.Button(main_frame, text="Сохранить учетные данные",
                  command=self.save_credentials, width=20).grid(
                    row=3, column=2, padx=10, pady=5, sticky='w')

        # Тип вопроса
        ttk.Label(main_frame, text="Тип вопроса:", font=self.bold_font).grid(
            row=4, column=0, sticky='w', padx=10, pady=(15, 5))

        self.question_type = tk.StringVar(value="string")

        types_frame = ttk.Frame(main_frame)
        types_frame.grid(row=4, column=1, columnspan=2, sticky='w', padx=10, pady=5)

        types = [
            ("Текстовый ввод", "string"),
            ("Выбор одного", "radio"),
            ("Выбор нескольких", "checkbox"),
            ("Выпадающий список", "select"),
            ("Сопоставление", "matching"),
            ("Числовой ввод", "number")
        ]

        for i, (text, value) in enumerate(types):
            rb = ttk.Radiobutton(types_frame, text=text, variable=self.question_type,
                                value=value, command=self.on_question_type_change)
            rb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)

    def create_brute_tab(self):
        """Настройки строкового перебора"""
        brute_frame = ttk.Frame(self.notebook)
        self.notebook.add(brute_frame, text="Строковый перебор")

        # Символы для перебора
        ttk.Label(brute_frame, text="Символы для перебора:", font=self.bold_font).grid(
            row=0, column=0, sticky='w', padx=10, pady=(15, 5))

        self.chars_entry = ttk.Entry(brute_frame, width=50, font=self.normal_font)
        self.chars_entry.grid(row=0, column=1, padx=10, pady=(15, 5), sticky='we')
        self.chars_entry.insert(0, "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

        # Быстрые наборы символов
        presets_frame = ttk.LabelFrame(brute_frame, text="Быстрые наборы символов")
        presets_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=10, pady=10)

        presets = [
            ("Цифры", "0123456789"),
            ("Буквы (нижние)", "abcdefghijklmnopqrstuvwxyz"),
            ("Буквы (верхние)", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            ("Буквы все", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            ("Цифры+буквы", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            ("Спецсимволы", "!@#$%^&*()_+-=[]{}|;:,.<>?")
        ]

        for i, (name, chars) in enumerate(presets):
            ttk.Button(presets_frame, text=name, width=15,
                      command=lambda c=chars: self.chars_entry.insert(tk.END, c)).grid(
                        row=i//3, column=i%3, padx=5, pady=5)

        # Длина строки
        ttk.Label(brute_frame, text="Длина строки:", font=self.bold_font).grid(
            row=2, column=0, sticky='w', padx=10, pady=(10, 5))

        length_frame = ttk.Frame(brute_frame)
        length_frame.grid(row=2, column=1, sticky='w', padx=10, pady=(10, 5))

        ttk.Label(length_frame, text="От:").pack(side='left', padx=(0, 5))
        self.min_len_spinbox = ttk.Spinbox(length_frame, from_=1, to=50, width=8)
        self.min_len_spinbox.pack(side='left', padx=5)
        self.min_len_spinbox.set(1)

        ttk.Label(length_frame, text="До:").pack(side='left', padx=(20, 5))
        self.max_len_spinbox = ttk.Spinbox(length_frame, from_=1, to=50, width=8)
        self.max_len_spinbox.pack(side='left', padx=5)
        self.max_len_spinbox.set(5)

        # Задержка между попытками
        ttk.Label(brute_frame, text="Задержка между попытками:", font=self.bold_font).grid(
            row=3, column=0, sticky='w', padx=10, pady=(10, 5))

        delay_frame = ttk.Frame(brute_frame)
        delay_frame.grid(row=3, column=1, sticky='w', padx=10, pady=(10, 5))

        self.delay_spinbox = ttk.Spinbox(delay_frame, from_=0.1, to=10, increment=0.1, width=8)
        self.delay_spinbox.pack(side='left', padx=5)
        self.delay_spinbox.set(1.0)
        ttk.Label(delay_frame, text="секунд").pack(side='left', padx=5)

    def create_number_tab(self):
        """Настройки числового перебора"""
        number_frame = ttk.Frame(self.notebook)
        self.notebook.add(number_frame, text="Числовой перебор")

        # Начальное значение
        ttk.Label(number_frame, text="Начальное значение:", font=self.bold_font).grid(
            row=0, column=0, sticky='w', padx=10, pady=(15, 5))

        self.start_number_entry = ttk.Entry(number_frame, width=20, font=self.normal_font)
        self.start_number_entry.grid(row=0, column=1, sticky='w', padx=10, pady=(15, 5))
        self.start_number_entry.insert(0, "0")

        # Конечное значение
        ttk.Label(number_frame, text="Конечное значение:", font=self.bold_font).grid(
            row=1, column=0, sticky='w', padx=10, pady=5)

        self.end_number_entry = ttk.Entry(number_frame, width=20, font=self.normal_font)
        self.end_number_entry.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        self.end_number_entry.insert(0, "100")

        # Шаг перебора
        ttk.Label(number_frame, text="Шаг перебора:", font=self.bold_font).grid(
            row=2, column=0, sticky='w', padx=10, pady=5)

        step_frame = ttk.Frame(number_frame)
        step_frame.grid(row=2, column=1, sticky='w', padx=10, pady=5)

        self.step_entry = ttk.Entry(step_frame, width=15, font=self.normal_font)
        self.step_entry.pack(side='left', padx=(0, 10))
        self.step_entry.insert(0, "1")

        # Выбор точности
        self.precision_var = tk.StringVar(value="0")
        ttk.Label(step_frame, text="Точность:").pack(side='left', padx=(10, 5))
        precision_menu = ttk.Combobox(step_frame, textvariable=self.precision_var,
                                      values=["0", "1", "2", "3", "4", "5"],
                                      width=5, state="readonly")
        precision_menu.pack(side='left')
        ttk.Label(step_frame, text="знаков").pack(side='left', padx=5)

        # Быстрые шаги
        ttk.Label(number_frame, text="Быстрые шаги:", font=self.bold_font).grid(
            row=3, column=0, sticky='w', padx=10, pady=5)

        quick_steps_frame = ttk.Frame(number_frame)
        quick_steps_frame.grid(row=3, column=1, sticky='w', padx=10, pady=5)

        steps = [("0.1", "0.1"), ("0.01", "0.01"), ("0.001", "0.001"),
                ("0.0001", "0.0001"), ("-1", "-1"), ("-0.1", "-0.1")]

        for i, (text, value) in enumerate(steps):
            ttk.Button(quick_steps_frame, text=text, width=8,
                      command=lambda v=value: self.step_entry.delete(0, tk.END) or self.step_entry.insert(0, v)).grid(
                        row=i//3, column=i%3, padx=2, pady=2)

        # Формат вывода
        ttk.Label(number_frame, text="Формат вывода:", font=self.bold_font).grid(
            row=4, column=0, sticky='w', padx=10, pady=5)

        self.number_format_var = tk.StringVar(value="auto")
        format_frame = ttk.Frame(number_frame)
        format_frame.grid(row=4, column=1, sticky='w', padx=10, pady=5)

        formats = [
            ("Авто", "auto"),
            ("Обычный", "normal"),
            ("Научный", "scientific"),
            ("Фиксированный", "fixed")
        ]

        for i, (text, value) in enumerate(formats):
            rb = ttk.Radiobutton(format_frame, text=text, variable=self.number_format_var, value=value)
            rb.grid(row=0, column=i, padx=5, pady=2)

        # Превью генерации
        ttk.Label(number_frame, text="Пример чисел:", font=self.bold_font).grid(
            row=5, column=0, sticky='w', padx=10, pady=(15, 5))

        self.preview_text = scrolledtext.ScrolledText(number_frame, height=8, width=60,
                                                      font=('Consolas', 9))
        self.preview_text.grid(row=5, column=1, padx=10, pady=(15, 5), sticky='we')

        ttk.Button(number_frame, text="Сгенерировать превью",
                  command=self.generate_preview).grid(row=6, column=1, sticky='w', padx=10, pady=5)

    def create_log_tab(self):
        """Лог выполнения"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Лог")

        # Панель управления логом
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill='x', padx=10, pady=(10, 5))

        controls = [
            ("Экспорт лога", self.export_log),
            ("Очистить лог", self.clear_log),
            ("Экспорт CSV", self.export_results),
            ("Копировать", self.copy_log),
            ("Поиск", self.search_log)
        ]

        for text, command in controls:
            ttk.Button(log_control_frame, text=text, command=command).pack(side='left', padx=2)

        # Лог
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=100,
                                                 font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)

        # Статусная строка лога
        self.log_status = ttk.Label(log_frame, text="Готов", relief=tk.SUNKEN)
        self.log_status.pack(fill='x', padx=10, pady=(5, 10))

    def create_scheduler_tab(self):
        """Планировщик"""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="Планировщик")

        # Список задач
        ttk.Label(schedule_frame, text="Запланированные задачи:", font=self.bold_font).pack(
            anchor='w', padx=10, pady=(10, 5))

        list_frame = ttk.Frame(schedule_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Список с прокруткой
        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side='right', fill='y')

        self.schedule_listbox = tk.Listbox(list_frame, height=10, width=90,
                                          font=self.normal_font,
                                          yscrollcommand=list_scroll.set,
                                          selectbackground='#0078d7')
        self.schedule_listbox.pack(side='left', fill='both', expand=True)
        list_scroll.config(command=self.schedule_listbox.yview)

        # Форма добавления
        form_frame = ttk.LabelFrame(schedule_frame, text="Добавить задачу")
        form_frame.pack(fill='x', padx=10, pady=10)

        # Дата и время
        ttk.Label(form_frame, text="Дата и время:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.schedule_datetime_entry = ttk.Entry(form_frame, width=20, font=self.normal_font)
        self.schedule_datetime_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.schedule_datetime_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        ttk.Button(form_frame, text="Сейчас",
                  command=lambda: self.schedule_datetime_entry.delete(0, tk.END) or
                                 self.schedule_datetime_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
                  ).grid(row=0, column=2, padx=5)

        # Повторение
        ttk.Label(form_frame, text="Повтор:").grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.repeat_var = tk.StringVar(value="none")
        repeats = [("Нет", "none"), ("Ежедневно", "daily"),
                  ("Еженедельно", "weekly"), ("Ежемесячно", "monthly")]

        for i, (text, value) in enumerate(repeats):
            ttk.Radiobutton(form_frame, text=text, variable=self.repeat_var,
                           value=value).grid(row=1, column=1+i, sticky='w', padx=5)

        # Кнопки управления
        button_frame = ttk.Frame(schedule_frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        buttons = [
            ("Добавить", self.add_schedule_task),
            ("Удалить", self.remove_schedule_task),
            ("Редактировать", self.edit_schedule_task),
            ("Запустить", self.start_scheduler),
            ("Остановить", self.stop_scheduler),
            ("Экспорт", self.export_schedule)
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side='left', padx=2)

        # Статус
        self.schedule_status = ttk.Label(schedule_frame, text="Планировщик остановлен",
                                        font=self.bold_font)
        self.schedule_status.pack(pady=5)

    def create_remote_tab(self):
        """Удаленный запуск"""
        remote_frame = ttk.Frame(self.notebook)
        self.notebook.add(remote_frame, text="Удаленный доступ")

        # Настройки подключения
        config_frame = ttk.LabelFrame(remote_frame, text="Настройки подключения")
        config_frame.pack(fill='x', padx=10, pady=10)

        # Хост
        ttk.Label(config_frame, text="Хост:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.remote_host_entry = ttk.Entry(config_frame, width=30, font=self.normal_font)
        self.remote_host_entry.grid(row=0, column=1, padx=5, pady=5, sticky='we')
        self.remote_host_entry.insert(0, self.config.get("remote_host", "localhost"))

        # Порт
        ttk.Label(config_frame, text="Порт:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.remote_port_entry = ttk.Entry(config_frame, width=10, font=self.normal_font)
        self.remote_port_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.remote_port_entry.insert(0, self.config.get("remote_port", "3000"))

        # Протокол
        ttk.Label(config_frame, text="Протокол:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.remote_protocol = tk.StringVar(value=self.config.get("remote_protocol", "ws"))
        ttk.Combobox(config_frame, textvariable=self.remote_protocol,
                    values=["ws", "wss", "http", "https"], width=10).grid(
                    row=2, column=1, sticky='w', padx=5, pady=5)

        # Кнопки тестирования
        test_frame = ttk.Frame(config_frame)
        test_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(test_frame, text="Проверить подключение",
                  command=self.test_remote_connection).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Сохранить настройки",
                  command=self.save_remote_settings).pack(side='left', padx=5)

        # Инструкция
        help_frame = ttk.LabelFrame(remote_frame, text="Инструкция по настройке")
        help_frame.pack(fill='x', padx=10, pady=10)

        help_text = """Для запуска удаленного Playwright выполните на сервере:

1. Установите Playwright: pip install playwright
2. Установите браузеры: playwright install
3. Запустите сервер: playwright run-server --port 3000

Или используйте команду Docker:
docker run -p 3000:3000 mcr.microsoft.com/playwright:latest 
playwright run-server --port 3000"""

        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT)
        help_label.pack(padx=10, pady=10)

        # Статус подключения
        self.remote_status = ttk.Label(remote_frame, text="Не подключено",
                                      font=self.bold_font)
        self.remote_status.pack(pady=10)

    def create_control_panel(self):
        """Панель управления"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=10)

        # Кнопки
        buttons = [
            ("Начать перебор", self.start_brute_force),
            ("Остановить", self.stop_brute_force),
            ("Тест связи", self.test_connection),
            ("Сохранить все", self.save_all_settings),
            ("Статистика", self.show_stats),
            ("Настройки", self.show_settings)
        ]

        for text, command in buttons:
            btn = ttk.Button(control_frame, text=text, command=command, width=18)
            btn.pack(side='left', padx=2)

        # Сохраняем ссылки на кнопки начала и остановки
        self.start_btn = control_frame.winfo_children()[0]
        self.stop_btn = control_frame.winfo_children()[1]
        self.stop_btn.config(state='disabled')

        # Прогресс-бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var,
                                          maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(pady=(0, 10))

        # Статус
        self.status_label = ttk.Label(self.root, text="Готов к работе",
                                     font=self.bold_font)
        self.status_label.pack(pady=5)

    # ========== ОСНОВНЫЕ МЕТОДЫ ==========

    def on_question_type_change(self):
        """При изменении типа вопроса"""
        qtype = self.question_type.get()
        if qtype == "number":
            self.notebook.tab(2, state="normal")  # Вкладка чисел
        else:
            self.notebook.tab(2, state="disabled")

    def generate_preview(self):
        """Генерация превью чисел"""
        try:
            start = float(self.start_number_entry.get())
            end = float(self.end_number_entry.get())
            step = float(self.step_entry.get())
            precision = int(self.precision_var.get())

            numbers = self.number_generator.generate_range(start, end, step, precision)

            self.preview_text.delete(1.0, tk.END)
            for i, num in enumerate(numbers[:50]):  # Показываем первые 50 чисел
                self.preview_text.insert(tk.END, f"{i+1}. {num}\n")

            if len(numbers) > 50:
                self.preview_text.insert(tk.END, f"\n... и еще {len(numbers)-50} чисел")

            total = len(numbers)
            self.log_message(f"Сгенерировано {total:,} чисел для перебора")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Некорректные параметры: {e}")

    def save_credentials(self):
        """Сохранение учетных данных"""
        self.config["email"] = self.email_entry.get()
        self.config["password"] = self.password_entry.get()
        self.config_manager.save_config(self.config)
        self.log_message("Учетные данные сохранены")

    def save_all_settings(self):
        """Сохранение всех настроек"""
        self.save_credentials()
        self.config_manager.save_history(self.history)
        self.config_manager.save_schedule(self.schedule_tasks)
        self.log_message("Все настройки сохранены")

    def save_remote_settings(self):
        """Сохранение удаленных настроек"""
        self.config["remote_host"] = self.remote_host_entry.get()
        self.config["remote_port"] = self.remote_port_entry.get()
        self.config["remote_protocol"] = self.remote_protocol.get()
        self.config_manager.save_config(self.config)
        self.log_message("Настройки удаленного доступа сохранены")

    def log_message(self, message):
        """Логирование сообщения"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Лог очищен")

    def copy_log(self):
        """Копирование лога"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get(1.0, tk.END))
        self.log_message("Лог скопирован в буфер")

    def search_log(self):
        """Поиск в логе"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Поиск в логе")
        search_window.geometry("400x150")

        ttk.Label(search_window, text="Поиск:").pack(pady=10)
        search_entry = ttk.Entry(search_window, width=40)
        search_entry.pack(pady=5)

        def search():
            text = self.log_text.get(1.0, tk.END)
            search_term = search_entry.get()
            if search_term:
                pos = text.find(search_term)
                if pos != -1:
                    self.log_text.tag_remove("search", 1.0, tk.END)
                    self.log_text.tag_add("search", f"1.0+{pos}c", f"1.0+{pos+len(search_term)}c")
                    self.log_text.tag_config("search", background="yellow")
                    self.log_text.see(f"1.0+{pos}c")
                    search_window.destroy()
                else:
                    messagebox.showinfo("Поиск", "Текст не найден")

        ttk.Button(search_window, text="Найти", command=search).pack(pady=10)

    def export_log(self):
        """Экспорт лога"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Лог экспортирован в {filename}")

    def export_results(self):
        """Экспорт результатов"""
        if not self.last_results:
            messagebox.showinfo("Нет данных", "Нет результатов для экспорта")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Дата", "URL", "Тип", "Результат", "Ответ", "Время"])
                    writer.writerows(self.last_results)
                self.log_message(f"Результаты экспортированы в {filename}")
            except Exception as e:
                self.log_message(f"Ошибка экспорта: {e}")

    def export_schedule(self):
        """Экспорт расписания"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.schedule_tasks, f, indent=2, ensure_ascii=False)
            self.log_message(f"Расписание экспортировано в {filename}")

    def update_history_listbox(self):
        """Обновление истории"""
        self.history_listbox.delete(0, tk.END)
        for url in self.history[:20]:
            self.history_listbox.insert(tk.END, url[:80] + ("..." if len(url) > 80 else ""))

    def on_history_select(self, event):
        """Выбор из истории"""
        selection = self.history_listbox.curselection()
        if selection:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.history[selection[0]])

    def update_schedule_display(self):
        """Обновление списка задач"""
        self.schedule_listbox.delete(0, tk.END)
        for task in self.schedule_tasks:
            status = "Повтор: " if task.get('repeat', 'none') != 'none' else ""
            text = f"{status}{task['datetime']} - {task['url'][:40]}..."
            self.schedule_listbox.insert(tk.END, text)

    # ========== ПЛАНИРОВЩИК ==========

    def add_schedule_task(self):
        """Добавление задачи"""
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL")
            return

        try:
            datetime.strptime(self.schedule_datetime_entry.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты")
            return

        task = {
            "datetime": self.schedule_datetime_entry.get(),
            "url": url,
            "type": self.question_type.get(),
            "repeat": self.repeat_var.get(),
            "email": self.email_entry.get(),
            "password": self.password_entry.get()
        }

        self.schedule_tasks.append(task)
        self.config_manager.save_schedule(self.schedule_tasks)
        self.update_schedule_display()
        self.log_message(f"Задача добавлена на {task['datetime']}")

    def remove_schedule_task(self):
        """Удаление задачи"""
        selection = self.schedule_listbox.curselection()
        if selection:
            del self.schedule_tasks[selection[0]]
            self.config_manager.save_schedule(self.schedule_tasks)
            self.update_schedule_display()
            self.log_message("Задача удалена")

    def edit_schedule_task(self):
        """Редактирование задачи"""
        selection = self.schedule_listbox.curselection()
        if selection:
            # Реализация редактирования
            pass

    def start_scheduler(self):
        """Запуск планировщика"""
        self.scheduled = True
        self.schedule_status.config(text="Планировщик запущен")
        self.log_message("Планировщик запущен")

        self.scheduler_thread = threading.Thread(target=self.scheduler.run, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """Остановка планировщика"""
        self.scheduled = False
        self.schedule_status.config(text="Планировщик остановлен")
        self.log_message("Планировщик остановлен")

    # ========== УДАЛЕННЫЙ ДОСТУП ==========

    def test_remote_connection(self):
        """Тест удаленного подключения"""
        def test():
            self.log_message("Тестирую удаленное подключение...")
            if self.remote_playwright.test_connection():
                self.remote_status.config(text="Подключено")
                self.log_message("Удаленное подключение успешно")
            else:
                self.remote_status.config(text="Ошибка подключения")

        threading.Thread(target=test, daemon=True).start()

    def test_connection(self):
        """Тест подключения к Stepik"""
        self.stepik_api.test_connection()

    # ========== ОСНОВНОЙ ПЕРЕБОР ==========

    def start_brute_force(self):
        """Запуск перебора"""
        if self.running:
            return

        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL")
            return

        # Добавляем в историю
        if url not in self.history:
            self.history.insert(0, url)
            if len(self.history) > 50:
                self.history = self.history[:50]
            self.update_history_listbox()

        self.running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="Выполняется перебор...")

        # Запуск в отдельном потоке
        self.brute_thread = threading.Thread(target=self.run_brute_force, daemon=True)
        self.brute_thread.start()

    def stop_brute_force(self):
        """Остановка перебора"""
        self.running = False
        self.status_label.config(text="Останавливается...")
        self.log_message("Остановка перебора...")

    def run_brute_force(self):
        """Основная логика перебора"""
        try:
            # Определяем тип перебора
            qtype = self.question_type.get()

            if qtype == "number":
                # Числовой перебор
                result = self.brute_logic.brute_number(
                    self.url_entry.get(),
                    self.email_entry.get(),
                    self.password_entry.get(),
                    float(self.start_number_entry.get()),
                    float(self.end_number_entry.get()),
                    float(self.step_entry.get()),
                    int(self.precision_var.get()),
                    float(self.delay_spinbox.get())
                )
            elif qtype == "string":
                # Строковый перебор
                result = self.brute_logic.brute_string(
                    self.url_entry.get(),
                    self.email_entry.get(),
                    self.password_entry.get(),
                    self.chars_entry.get(),
                    int(self.min_len_spinbox.get()),
                    int(self.max_len_spinbox.get()),
                    float(self.delay_spinbox.get())
                )
            else:
                # Другие типы
                result = self.brute_logic.brute_other(
                    self.url_entry.get(),
                    self.email_entry.get(),
                    self.password_entry.get(),
                    qtype,
                    float(self.delay_spinbox.get())
                )

            # Сохранение результата
            if result:
                self.save_result(result)

        except Exception as e:
            self.log_message(f"Ошибка: {str(e)[:200]}")
        finally:
            self.on_brute_finished()

    def save_result(self, result_data):
        """Сохранение результата"""
        self.last_results.append(result_data)

        # Сохранение в файл
        try:
            filename = "results.csv"
            file_exists = os.path.isfile(filename)

            with open(filename, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Дата", "URL", "Тип", "Результат", "Ответ", "Время"])
                writer.writerow(result_data)

            self.log_message(f"Результат сохранен в {filename}")
        except Exception as e:
            self.log_message(f"Ошибка сохранения: {e}")

    def on_brute_finished(self):
        """Завершение перебора"""
        self.running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Готов к работе")
        self.progress_var.set(0)

    def show_stats(self):
        """Показать статистику"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика")
        stats_window.geometry("400x300")

        total = len(self.last_results)
        success = len([r for r in self.last_results if r[3] == "Успешно"])

        stats_text = f"""
        Статистика выполнения:
        
        Всего попыток: {total}
        Успешных: {success}
        Неудачных: {total - success}
        Процент успеха: {success/total*100 if total > 0 else 0:.1f}%
        
        Последние 5 результатов:
        """

        for i, result in enumerate(self.last_results[-5:]):
            stats_text += f"\n{i+1}. {result[3]} - {result[4]}"

        ttk.Label(stats_window, text=stats_text, justify=tk.LEFT).pack(padx=20, pady=20)

    def show_settings(self):
        """Окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("500x400")

        ttk.Label(settings_window, text="Дополнительные настройки",
                 font=self.title_font).pack(pady=20)

        # Настройки прокси
        proxy_frame = ttk.LabelFrame(settings_window, text="Настройки прокси")
        proxy_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(proxy_frame, text="HTTP прокси:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(proxy_frame, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(proxy_frame, text="HTTPS прокси:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(proxy_frame, width=30).grid(row=1, column=1, padx=5, pady=5)