import requests
from loguru import logger
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class Notifier:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID

    def send_notification(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            logger.info(f"Отправлено уведомление")
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка при отправлении уведомления: {err}")

    def send_status_notification(self):
        self.send_notification("Бот работает")

    def send_file(self, file_path):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        files = {"document": open(file_path, "rb")}
        payload = {"chat_id": self.chat_id}
        try:
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            logger.info(f"Файл '{file_path}' успешно отправлен")
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка при отправлении файла: {err}")
