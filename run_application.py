import time
from loguru import logger
from browser import Browser
from config import IS_DEV, SECOND_URL, START_URL
from credentials_provider import DevCredentialsProvider, SMS365CredentialsProvider
from yandex_login import login_yandex


def run_application():
    logger.info("Старт")
    # Выбор поставщика учетных данных в зависимости от режима разработки
    if IS_DEV:
        credentials_provider = DevCredentialsProvider()
    else:
        credentials_provider = SMS365CredentialsProvider()

    while True:
        # Получение учетных данных
        logger.info("Получение данных для входа в яндекс")
        credentials = credentials_provider.get_credentials()
        logger.success("Данные для входа в Яндекс получены")

        browser = Browser()
        logger.info("Запуск браузера")
        browser.start_browser()

        try:
            # Попытка войти на сайт
            if login_yandex(
                browser,
                credentials_provider,
                credentials["login"],
                credentials["password"],
                credentials["activation_id"],
            ):
                logger.info("Вход выполнен успешно")
                browser.driver.get(START_URL)
                browser.driver.get(SECOND_URL)
                time.sleep(10)  # Подождем 10 секунд для наблюдения
                break  # Выходим из цикла, если вход успешен
            else:
                logger.info("Не удалось войти, пробуем снова...")
        finally:
            return browser.close_browser()
