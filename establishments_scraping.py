import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from loguru import logger
from browser import Browser
from config import (
    MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS,
)
from helpers import declension, is_address_match


def get_establishments(browser: Browser):
    """Функция для поиска и взаимодействия с заведениями"""
    retries = 0
    while retries < MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS:
        retries += 1
        logger.info(
            f"Попытка {retries}/{MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS} получения списка заведений"
        )

        establishments = try_get_establishments(browser)

        if not establishments and retries == MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS:
            logger.warning("Не удалось получить список заведений")
            break

        if not establishments:
            logger.warning("Не удалось получить список заведений. Повторная попытка...")
            browser.driver.refresh()
            time.sleep(5)
            continue

        return establishments

    logger.error(
        f"Не удалось получить список заведений после {MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS} {declension(MAX_GET_ESTABLISHMENTS_LIST_ATTEMPTS, 'попытки', 'попыток', 'попыток')}"
    )
    return


def get_target_establishment_index(
    establishments: list,
    establishment_name: str,
    establishment_address: str,
):
    """Функция для поиска целевого заведения"""
    for index, establishment in enumerate(establishments):
        try:
            name = establishment.find_element(
                By.CSS_SELECTOR, ".search-business-snippet-view__title"
            ).text
            address = establishment.find_element(
                By.CSS_SELECTOR, ".search-business-snippet-view__address"
            ).text
            if (
                name.lower().strip() == establishment_name.lower().strip()
                and is_address_match(address, establishment_address)
            ):
                return index
        except Exception as e:
            logger.warning(
                f"Не удалось получить целевое заведение на индексе {index}, {e}"
            )
    logger.warning(f"Заведение с именем '{establishment_name}' не найдено")
    return -1


def try_get_establishments(browser):
    """Пробует получить список заведений, возвращает его или None в случае неудачи"""
    try:
        logger.info(f"Попытка получить список всех заведений")
        scroll_through_establishments(browser)
        establishments = find_establishments(browser)
        return establishments
    except TimeoutException:
        logger.error("Ошибка: время ожидания истекло при получении списка заведений")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении списка заведений: {e}")


def close_tooltip_popup_by_title(browser):
    """Ищет попап с заголовком 'Взгляните!' и закрывает его, если найден"""
    try:
        # Ожидание появления заголовка с текстом 'Взгляните!'
        title_element = WebDriverWait(browser.driver, 5).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class, 'tooltip-content-view__title') and text()='Взгляните!']",
                )
            )
        )
        # Поиск ближайшего попапа-контейнера относительно заголовка
        popup = title_element.find_element(
            By.XPATH, "./ancestor::div[contains(@class, 'popup')]"
        )
        # Находим кнопку закрытия внутри попапа и кликаем на нее
        close_button = popup.find_element(By.CSS_SELECTOR, "button.close-button")
        close_button.click()
        logger.info("Попап успешно закрыт")

    except TimeoutException:
        logger.info("Попап не найден, продолжаем выполнение")
    except NoSuchElementException as e:
        logger.error(f"Ошибка: не удалось найти кнопку закрытия в попапе, {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при закрытии попапа: {e}")


def scroll_through_establishments(browser: Browser):
    """Прокручивает контейнер с заведениями на странице, чтобы загрузились все заведения"""
    try:
        scroll_container = WebDriverWait(browser.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "scroll__container"))
        )
        previous_height = browser.driver.execute_script(
            "return arguments[0].scrollHeight", scroll_container
        )
        while True:
            # Прокрутите контейнер до самого низа
            browser.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container
            )
            # Подождите несколько секунд для загрузки новых элементов
            time.sleep(2)
            # Получите новую высоту контейнера
            new_height = browser.driver.execute_script(
                "return arguments[0].scrollHeight", scroll_container
            )
            # Проверьте, изменилась ли высота
            if new_height == previous_height:
                browser.driver.execute_script(
                    "arguments[0].scrollTop = 0;", scroll_container
                )
                break  # Если высота не изменилась, значит достигнут конец списка
            previous_height = new_height
    except WebDriverException as e:
        logger.error(f"Ошибка при прокрутке списка заведений: {e}")
        raise


def find_establishments(browser: Browser):
    """Ищет и возвращает список заведений как элементы страницы"""
    try:
        elements = WebDriverWait(browser.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "search-snippet-view"))
        )

        # Фильтруем только заведения с классом '_type_business', чтобы не попадались подборки
        business_establishments = []
        for element in elements:
            # Находим вложенный элемент с нужным классом
            body_div = element.find_element(By.CLASS_NAME, "search-snippet-view__body")
            if "_type_business" in body_div.get_attribute("class"):
                business_establishments.append(element)

        logger.info(f"Найдено {len(business_establishments)} заведений")

        return business_establishments
    except TimeoutException:
        logger.warning("Не удалось найти заведения на странице")
        return []
