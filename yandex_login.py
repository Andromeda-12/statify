import pickle
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from browser import Browser
from config import (
    ACCOUNT_FIRSTNAME,
    ACCOUNT_LASTNAME,
    IS_DEV,
    TEST_ACCOUNT_COOKIE_FILE_NAME,
)
from credentials_provider import (
    CredentialsProvider,
    DevCredentialsProvider,
    SMS365CredentialsProvider,
)


def login_to_yandex_account(browser: Browser):
    """Выполнить вход в аккаунт Яндекс."""
    try:
        if IS_DEV:
            browser.start_browser()
            browser.driver.get("https://yandex.ru/maps")
            return
        
        try_login_with_credentials(browser)

        if not check_is_successful_logged_in(browser):
            raise RuntimeError("Не удалось войти в аккаунт.")

    except Exception as e:
        logger.error(f"Ошибка при входе в Яндекс: {e}")
        if browser.is_open:
            browser.close_browser()
        raise


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

        if login(
            browser,
            credentials_provider,
            credentials["login"],
            credentials["password"],
            credentials["activation_id"],
        ):
            logger.info("Вход выполнен успешно")
            break  # Выходим из цикла, если вход успешен
        else:
            browser.close_browser()
            logger.info("Не удалось войти, пробуем снова...")


def try_login_with_cookies(browser: Browser, cookies):
    browser.start_browser()
    browser.driver.get("https://id.yandex.ru/")
    time.sleep(1)
    add_cookies_to_browser(browser, cookies)
    time.sleep(1)
    browser.driver.get("https://id.yandex.ru/")

    try:
        browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="profile-card-avatar"]')
            )
        )
        logger.success("Успешный вход с помощью кук")
    except Exception as e:
        logger.error(f"Не получилось войти с помощью кук: {e}")


def login(
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

            if IS_DEV:
                # Возвращаем True или False, в зависимости от того, получилось ли войти в аккаунт
                return is_dev_account_login_by_email(browser, password)

            # Пытаемся получить смс
            sms_code = credentials_provider.get_sms_code(
                activation_id=activation_id,
                retry_action=lambda: retry_send_sms(browser),
            )

            if sms_code is None:
                logger.info("Код активации не получен")
                return False

            handle_enter_phone_code(browser, sms_code)

            logger.info("Вход в аккаунт")
            return is_account_registration_and_login(browser, password)

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
    except Exception as e:
        logger.error(f"Не получилось отправить новое смс: {e}")


def is_dev_account_login_by_email(browser: Browser, password: str):
    """
    Получилось ли войти в тестовый аккаунт

    :return: True, если получилось войти, иначе False
    """
    try:
        logger.info("Логика входа в тестовый аккаунт")
        password_field = browser.wait_for_condition(
            EC.presence_of_element_located((By.ID, "passp-field-passwd"))
        )
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        logger.info("Введен пароль")
        logger.info("Введите код активации, полученный на телефон в пуш уведомлении: ")
        code = input("Код активации: ").strip()

        if not code:
            logger.info("Код активации не был введен")
            return False

        handle_enter_phone_code(browser, code)

        return check_is_logged_in(browser)

    except Exception as e:
        logger.error(f"Ошибка при попытке войти в тестовый аккаунт: {e}")
        return False


def check_is_logged_in(browser: Browser):
    try:
        browser.wait_for_condition(EC.url_to_be("https://id.yandex.ru/"))
        logger.success("Вход в аккаунт успешно выполнен")

        if IS_DEV:
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


def is_dev_account_login_by_phone(browser: Browser, password: str):
    """
    Получилось ли войти в тестовый аккаунт

    :return: True, если получилось войти, иначе False
    """
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

        return check_is_logged_in(browser)

    except Exception as e:
        logger.error(f"Ошибка при попытке войти в тестовый аккаунт: {e}")
        return False


def is_account_registration_and_login(browser: Browser, password: str):
    """
    Получилось ли зарегистрироваться и войти в аккаунт

    :return: True, если получилось войти, иначе False
    """
    try:
        firstname_field = browser.wait_for_condition(
            EC.presence_of_element_located((By.ID, "passp-field-firstname"))
        )
        firstname_field.send_keys(ACCOUNT_FIRSTNAME)
        logger.info(f"Введено имя")

        lastname_field = browser.wait_for_condition(
            EC.presence_of_element_located((By.ID, "passp-field-lastname"))
        )
        lastname_field.send_keys(ACCOUNT_LASTNAME)
        lastname_field.send_keys(Keys.RETURN)
        logger.info(f"Введена фамилия")

        # Далее
        handle_action_button(browser)
        # Создать аккаунт
        handle_create_account_button(browser)
        # Принимаю
        handle_action_button(browser)
        # Не сейчас
        handle_button_not_now(browser)

        return check_is_logged_in(browser)

    except Exception as e:
        logger.error(f"Ошибка при попытке войти в аккаунт: {e}")
        return False


def handle_enter_phone_code(browser: Browser, code):
    try:
        # Вставляем полученный код
        phone_code_field = browser.wait_for_condition(
            EC.presence_of_element_located((By.ID, "passp-field-phoneCode"))
        )
        phone_code_field.send_keys(code)
        phone_code_field.send_keys(Keys.RETURN)
        logger.info("Введен код активации")
    except:
        logger.error(f"Поле для ввода кода не появилось")


def handle_create_account_button(browser: Browser):
    try:
        # Ожидаем, когда кнопка "Создать аккаунт" станет кликабельной
        browser.wait_for_condition(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-t="button:default:accounts: createIDBtn"]')
            )
        )
        create_account_button = browser.driver.find_element(
            By.CSS_SELECTOR, 'button[data-t="button:default:accounts: createIDBtn"]'
        )
        create_account_button.click()
        logger.info(f'Нажата кнопка "Создать аккаунт"')
    except:
        logger.error(f'Кнопка "Создать аккаунт" не появилась')


def handle_action_button(browser: Browser):
    try:
        # Ожидаем, когда кнопка "Далее" станет кликабельной
        browser.wait_for_condition(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-t="button:action"]'))
        )
        action_button = browser.driver.find_element(
            By.CSS_SELECTOR, '[data-t="button:action"]'
        )
        action_button.click()
        logger.info(f'Нажата кнопка "Далее"')
    except:
        logger.error(f'Кнопка "Далее" не появилась')


def handle_button_not_now(browser: Browser):
    try:
        # Находим кнопку "Не сейчас"
        button = browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-t="button:pseudo"]')
            )
        )
        button.click()
        logger.info(f'Нажата кнопка "Не сейчас"')
    except:
        logger.error(f'Кнопка "Не сейчас" не появилась')


def check_is_successful_logged_in(browser: Browser):
    try:
        browser.driver.get("https://yandex.ru/maps")
        browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".user-menu-control__icon._auth")
            )
        )
        logger.success("Вход был выполнен успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке на вход: {e}")
        return False


def add_cookies_to_browser(browser: Browser, cookies):
    try:
        for cookie in cookies:
            browser.driver.add_cookie(cookie)
        logger.info("Куки добавлены")
    except Exception as e:
        logger.error(f"Не удалось добавить куки: {e}")


def load_cookies():
    try:
        with open(TEST_ACCOUNT_COOKIE_FILE_NAME, "rb") as file:
            cookies = pickle.load(file)
            return cookies
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        logger.warning(f"Ошибка при загрузке куки: {e}")
        return None
