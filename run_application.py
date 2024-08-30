import pickle
import time
from loguru import logger
from browser import Browser
from config import IS_DEV, TEST_ACCOUNT_COOKIE_FILE_NAME
from yandex_login import (
    check_is_successful_logged_in,
    try_login_with_cookies,
    try_login_with_credentials,
)


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
                try_login_with_cookies(browser, cookies)
        else:
            # Пытаемся получить данные для входа, после удачной попытки браузер уже будет открыт
            try_login_with_credentials(browser)

        if not check_is_successful_logged_in(browser):
            return

        # Браузер уже открыт, повторно открывать не нужно
        browser.driver.get("https://yandex.ru/maps")
        logger.info(f"Открыты карты яндекса")

        time.sleep(60)
    except Exception as e:
        logger.error(e)
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
