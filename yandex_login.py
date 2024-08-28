import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from browser import Browser
from credentials_provider import CredentialsProvider


def login_yandex(
    browser: Browser,
    credentials_provider: CredentialsProvider,
    username: str,
    password: str,
    activation_id: str,
):
    try:
        logger.info("Открытие страницы авторизации яндекса")
        browser.driver.get("https://passport.yandex.ru/auth")
        # Логика входа на сайт
        try:
            login_field = browser.wait_for_condition(
                EC.presence_of_element_located((By.ID, "passp-field-login"))
            )
            login_field.send_keys(username)
            login_field.send_keys(Keys.RETURN)
            logger.info("Введен логин")
            # После этого нужно ввести смс
            # Пытаемся получить смс
            sms_code = credentials_provider.get_sms_code(
                activation_id=activation_id,
                retry_action=lambda: retry_send_sms(browser),
            )

            if sms_code is None:
                logger.info("Код активации не получен")
                return False

            # Вставляем полученный код
            phone_code_field = browser.wait_for_condition(
                EC.presence_of_element_located((By.ID, "passp-field-phoneCode"))
            )
            phone_code_field.send_keys(sms_code)
            phone_code_field.send_keys(Keys.RETURN)
            logger.info("Введен код активации")
            return True

        except Exception as e:
            logger.error(f"Ошибка при попытке ввести логин или пароль: {e}")
            raise  # Переброс исключения для последующей обработки

    except Exception as e:
        logger.error(f"Ошибка при входе на Яндекс: {e}")
        raise  # Переброс исключения для последующей обработки


def retry_send_sms(browser: Browser):
    try:
        retry_button = browser.wait_for_condition(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    'button[data-t="button:default:retry-to-request-code"]',
                )
            )
        )
        retry_button.click()
        logger.info("Запрос на повторную отправку СМС")
        time.sleep(30)  # Ждем 30 секунд перед повторной попыткой
    except Exception as e:
        logger.error(f"Не получилось отправить новое смс: {e}")
