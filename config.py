import os
import argparse
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="Run application.")
    parser.add_argument("--dev", action="store_true", help="run in development mode")
    return parser.parse_args()


args = parse_args()

# Флаг для режима разработки
IS_DEV = args.dev

# Путь к драйверу
EDGE_DRIVER_PATH = os.getenv("EDGE_DRIVER_PATH")

# Информация для Telegram-бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# API-ключ для 365sms
API_365SMS_KEY = os.getenv("API_365SMS_KEY")

# Данные для нового аккаунта
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
ACCOUNT_FIRSTNAME = "Иван"
ACCOUNT_LASTNAME = "Иванов"

# Данные для входа в тестовый аккаунт
TEST_ACCOUNT_USERNAME = os.getenv("TEST_ACCOUNT_USERNAME")
TEST_ACCOUNT_PASSWORD = os.getenv("TEST_ACCOUNT_PASSWORD")
TEST_ACCOUNT_COOKIE_FILE_NAME = "test_account_cookie"

# Время запуска приложения и отправки уведомлений
APPLICATION_RUN_TIME = os.getenv("APPLICATION_RUN_TIME")
SEND_STATUS_NOTIFICATION_TIME = os.getenv("SEND_STATUS_NOTIFICATION_TIME")

# Время, которое браузер ждет выполнения условия (поиск элементов)
BROWSER_CONDITION_WAIT_TIME = 30

# Количество попыток, сколько раз пытаемся обработать заведение в случае ошибки
MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS = 5

# Количество попыток для получения списков заведения
MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS = 2
# Количество попыток для получения целевого заведения в списке заведений
MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS = 2

# Количество заведений, которое будет просмотрено перед целевым заведением
MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET = 5
# Количество, сколько раз нужно посмотреть отзывы
# Максимальное количество, сколько нужно раз нажать на кнопку зума
MAX_ZOOM_TIMES = 5
