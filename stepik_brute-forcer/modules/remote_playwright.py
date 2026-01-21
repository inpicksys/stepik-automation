"""
Управление удаленным Playwright
"""
import threading
from playwright.sync_api import sync_playwright
import websocket
import json


class RemotePlaywright:
    def __init__(self, app):
        self.app = app
        self.connected = False

    def get_connection_string(self):
        """Получение строки подключения"""
        protocol = self.app.config.get("remote_protocol", "ws")
        host = self.app.config.get("remote_host", "localhost")
        port = self.app.config.get("remote_port", "3000")

        return f"{protocol}://{host}:{port}"

    def test_connection(self):
        """Тестирование подключения"""
        try:
            ws_url = self.get_connection_string()
            ws = websocket.create_connection(ws_url, timeout=5)
            ws.close()
            return True
        except Exception as e:
            self.app.log_message(f"❌ Ошибка подключения: {e}")
            return False

    def connect(self):
        """Подключение к удаленному браузеру"""
        try:
            ws_url = self.get_connection_string()

            with sync_playwright() as p:
                # Подключение к удаленному браузеру
                browser = p.chromium.connect_over_cdp(ws_url)

                # Или для более новых версий:
                # browser = p.chromium.connect(ws_url)

                self.connected = True
                self.app.log_message("✓ Подключено к удаленному браузеру")
                return browser

        except Exception as e:
            self.app.log_message(f"❌ Ошибка подключения к удаленному браузеру: {e}")
            return None

    def launch_remote_server(self):
        """Запуск сервера Playwright на удаленной машине"""
        # Эта функция может использоваться для автоматического запуска сервера
        # через SSH или другие протоколы
        pass

    def get_browser_list(self):
        """Получение списка доступных браузеров"""
        try:
            ws_url = self.get_connection_string()
            ws = websocket.create_connection(ws_url)

            # Запрос списка браузеров
            ws.send(json.dumps({
                "id": 1,
                "method": "Browser.getVersion"
            }))

            response = ws.recv()
            ws.close()

            return json.loads(response)
        except Exception as e:
            self.app.log_message(f"Ошибка получения списка браузеров: {e}")
            return None