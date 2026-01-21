"""
Управление конфигурацией и данными
"""
import json
import os
from cryptography.fernet import Fernet


class ConfigManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Шифрование
        self.key_file = os.path.join(data_dir, "key.key")
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self):
        """Получение или создание ключа шифрования"""
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key

    def encrypt(self, data):
        """Шифрование данных"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data):
        """Дешифрование данных"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def load_config(self):
        """Загрузка конфигурации"""
        config_file = os.path.join(self.data_dir, "config.json")

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Дешифровка пароля
                if "password" in config and config["password"]:
                    try:
                        config["password"] = self.decrypt(config["password"])
                    except:
                        pass  # Пароль не зашифрован

                return config
            except:
                pass

        # Конфигурация по умолчанию
        return {
            "email": "",
            "password": "",
            "remote_host": "localhost",
            "remote_port": "3000",
            "remote_protocol": "ws",
            "use_remote": False
        }

    def save_config(self, config):
        """Сохранение конфигурации"""
        config_file = os.path.join(self.data_dir, "config.json")

        # Шифровка пароля
        config_copy = config.copy()
        if "password" in config_copy and config_copy["password"]:
            config_copy["password"] = self.encrypt(config_copy["password"])

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_copy, f, indent=2, ensure_ascii=False)

    def load_history(self):
        """Загрузка истории"""
        history_file = os.path.join(self.data_dir, "history.json")

        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return []

    def save_history(self, history):
        """Сохранение истории"""
        history_file = os.path.join(self.data_dir, "history.json")

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history[:100], f, indent=2, ensure_ascii=False)

    def load_schedule(self):
        """Загрузка расписания"""
        schedule_file = os.path.join(self.data_dir, "schedule.json")

        if os.path.exists(schedule_file):
            try:
                with open(schedule_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        return []

    def save_schedule(self, schedule):
        """Сохранение расписания"""
        schedule_file = os.path.join(self.data_dir, "schedule.json")

        with open(schedule_file, "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)