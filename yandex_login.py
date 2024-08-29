import pickle
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from browser import Browser
from config import IS_DEV, TEST_ACCOUNT_COOKIE_FILE_NAME
from credentials_provider import (
    CredentialsProvider,
    DevCredentialsProvider,
    SMS365CredentialsProvider,
)


def try_login_with_credentials(browser: Browser):
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

        logger.info("Запуск браузера")
        browser.start_browser()

        if login_yandex(
            browser,
            credentials_provider,
            credentials["login"],
            credentials["password"],
            credentials["activation_id"],
        ):
            logger.info("Вход выполнен успешно")
            break  # Выходим из цикла, если вход успешен
        else:
            logger.info("Не удалось войти, пробуем снова...")


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

            if IS_DEV:
                # Возвращаем True или False, в зависимости от того, получилось ли войти в аккаунт
                return is_dev_account_login(browser, password)

            logger.info("Вход в аккаунт")
            return is_account_registration_and_login()

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


def is_dev_account_login(browser: Browser, password: str):
    try:
        logger.info("Логика входа в тестовый аккаунт")
        accounts_list_div = browser.wait_for_condition(
            EC.presence_of_element_located((By.CLASS_NAME, "Accounts-list"))
        )
        first_link = accounts_list_div.find_element(By.TAG_NAME, "a")
        first_link.click()
        logger.info("Клик на тестовый аккаунт")
        password_field = browser.wait_for_condition(
            EC.presence_of_element_located((By.ID, "passp-field-passwd"))
        )
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        logger.info("Введен пароль")

        handle_button_not_now()

        try:
            browser.wait_for_condition(EC.url_to_be("https://id.yandex.ru/"))
            logger.success("Вход в аккаунт успешно выполнен")
            pickle.dump(
                browser.driver.get_cookies(), open(TEST_ACCOUNT_COOKIE_FILE_NAME, "wb")
            )
            logger.info(f"Куки записаны в файл {TEST_ACCOUNT_COOKIE_FILE_NAME}")
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при ожидании перехода на страницу https://id.yandex.ru/: {e}"
            )
            return False

    except Exception as e:
        logger.error(f"Ошибка при попытке войти в тестовый аккаунт: {e}")
        return False
    
def is_account_registration_and_login(browser: Browser, password: str):
    pass


def handle_button_not_now(browser: Browser):
    try:
        # Находим кнопку "НЕ СЕЙЧАС"
        button = browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-t="button:pseudo"]')
            )
        )
        button.click()
    except:
        logger.warning(f'Кнопка "НЕ СЕЙЧАС" не появилась')
