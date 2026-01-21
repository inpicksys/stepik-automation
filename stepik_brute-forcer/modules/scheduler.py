"""
Планировщик задач
"""
import threading
import time
from datetime import datetime, timedelta
import schedule


class TaskScheduler:
    def __init__(self, app):
        self.app = app
        self.running = False

    def run(self):
        """Запуск планировщика"""
        self.running = True

        while self.running and self.app.scheduled:
            current_time = datetime.now()

            for task in self.app.schedule_tasks[:]:
                try:
                    task_time = datetime.strptime(task["datetime"], "%Y-%m-%d %H:%M")

                    # Проверка времени выполнения
                    if current_time >= task_time and current_time < task_time + timedelta(minutes=1):
                        self.app.log_message(f"⏰ Запуск запланированной задачи: {task['url']}")

                        # Выполнение задачи в отдельном потоке
                        thread = threading.Thread(
                            target=self.execute_task,
                            args=(task,),
                            daemon=True
                        )
                        thread.start()

                        # Обновление времени для повторяющихся задач
                        self.update_task_time(task)

                except Exception as e:
                    self.app.log_message(f"Ошибка обработки задачи: {e}")

            time.sleep(30)  # Проверка каждые 30 секунд

    def execute_task(self, task):
        """Выполнение задачи"""
        # Здесь можно вызвать соответствующий метод перебора
        # Например: self.app.brute_logic.brute_number(...)
        pass

    def update_task_time(self, task):
        """Обновление времени задачи для повторений"""
        repeat = task.get("repeat", "none")
        task_time = datetime.strptime(task["datetime"], "%Y-%m-%d %H:%M")

        if repeat == "daily":
            task["datetime"] = (task_time + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        elif repeat == "weekly":
            task["datetime"] = (task_time + timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
        elif repeat == "monthly":
            # Простое прибавление месяца
            month = task_time.month + 1
            year = task_time.year
            if month > 12:
                month = 1
                year += 1

            try:
                task["datetime"] = datetime(
                    year, month, task_time.day,
                    task_time.hour, task_time.minute
                ).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                # Если день не существует в следующем месяце
                task["datetime"] = datetime(
                    year, month, 1,
                    task_time.hour, task_time.minute
                ).strftime("%Y-%m-%d %H:%M")

        # Сохранение обновленного расписания
        self.app.config_manager.save_schedule(self.app.schedule_tasks)
        self.app.update_schedule_display()