import pickle
import time
from loguru import logger
from browser import Browser
from config import IS_DEV, SECOND_URL, START_URL, TEST_ACCOUNT_COOKIE_FILE_NAME
from yandex_login import try_login_with_credentials


def run_application():
    logger.info("Старт")
    browser = Browser()

    try:
        if IS_DEV:
            logger.info("Получение кук для тестового аккаунта")
            cookies = load_cookies()
            if cookies is None:
                logger.info("Куков нет, попытка залогиниться в яндекс")
                # Пытаемся получить данные для входа, после удачной попытки браузер уже будет открыт
                try_login_with_credentials(browser)
            else:
                logger.info("Куки есть, устанавливаем их браузеру")
                add_cookies_to_browser(browser)
        else:
            # Пытаемся получить данные для входа, после удачной попытки браузер уже будет открыт
            try_login_with_credentials(browser)

        # Браузер уже открыт, повторно открывать не нужно

        browser.driver.get("https://yandex.ru/maps")
        logger.info(f"Открыты карты яндекса")

        time.sleep(60)
    finally:
        if browser.is_open:
            browser.close_browser()
        return


def load_cookies():
    try:
        with open(TEST_ACCOUNT_COOKIE_FILE_NAME, "rb") as file:
            cookies = pickle.load(file)
            return cookies
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        logger.warning(f"Ошибка при загрузке куки: {e}")
        return None


def add_cookies_to_browser(browser: Browser, cookies):
    for cookie in cookies:
        browser.driver.add_cookie(cookie)
