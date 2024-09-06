import random
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from browser import Browser
from config import MAX_BROWSE_ESTABLISHMENTS_REVIEWS_ITERATIONS


def interact_with_establishment(browser: Browser, establishment: WebElement):
    title_element = establishment.find_element(
        By.CLASS_NAME, "search-business-snippet-view__title"
    )
    title = title_element.text
    logger.info(f"Взаимодействие с заведением '{title}'")

    open_establishment_card(browser, establishment)
    browse_establishment_photos(browser)
    browse_establishment_reviews_multiple_times(browser)


def interact_with_target_establishment(
    browser: Browser, target_establishment: WebElement
):
    interact_with_establishment(browser, target_establishment)
    open_establishment_overview(browser)
    perform_target_action(browser)


def open_establishment_card(browser: Browser, establishment: WebElement):
    try:
        # Кликаем на заведение
        establishment.click()
        # Ждем, когда откроется карточка с информацией о заведении
        browser.wait_for_condition(
            EC.presence_of_element_located((By.CLASS_NAME, "business-card-view")), 10
        )
        logger.info("Карточка заведения успешно открыта")
    except Exception as e:
        logger.error(f"Не удалось открыть карточку заведения: {e}")
        raise


def open_establishment_overview(browser: Browser):
    try:
        # Находим кнопку обзор
        overview_button = browser.wait_for_condition(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div._name_overview")),
            10,
        )
        browser.scroll_to(overview_button)
        time.sleep(2)
        logger.info('Клик по кнопке "Обзор"')
        overview_button.click()
        time.sleep(1)
    except Exception as e:
        logger.error(f"Не удалось найти или нажать на кнопку обзор: {e}")
        time.sleep(30)
        raise


def browse_establishment_photos(browser: Browser):
    try:
        # Находим кнопку фотографий
        photos_button = browser.wait_for_condition(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div._name_gallery")),
            10,
        )
        browser.scroll_to(photos_button)
        time.sleep(2)
        logger.info("Клик по кнопке с фото")
        photos_button.click()
        time.sleep(1)
    except Exception as e:
        logger.error(f"Не удалось найти или нажать на кнопку фотографий: {e}")
        raise

    try:
        # Проверка наличия элемента с фото
        photo_element = browser.wait_for_condition(
            EC.presence_of_element_located((By.CLASS_NAME, "media-wrapper")), 10
        )
        logger.info("Клик по фото")
        photo_element.click()
        time.sleep(2)
        browser.driver.back()
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Элемент с фото не найден, возможно, фото отсутствуют: {e}")
        raise

    logger.success("Фото просмотрены")


def browse_establishment_reviews_multiple_times(browser: Browser):
    for iteration in range(MAX_BROWSE_ESTABLISHMENTS_REVIEWS_ITERATIONS):
        try:
            browse_establishment_reviews(browser)
        except Exception as e:
            logger.error(f"Ошибка при просмотре отзывов на {iteration} итерации")
    logger.success(f"Отзывы просмотрены")


def browse_establishment_reviews(browser: Browser):
    try:
        # Находим кнопку отзывов
        reviews_button = browser.wait_for_condition(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div._name_reviews")),
            10,
        )
        browser.scroll_to(reviews_button)
        time.sleep(2)
        logger.info("Клик по отзывам")
        reviews_button.click()
        time.sleep(5)
    except Exception as e:
        logger.error(f"Не удалось найти или нажать на кнопку отзывов: {e}")
        raise

    try:
        # Находим селект выбора сортировки отзывов
        order_select_element = browser.wait_for_condition(
            EC.element_to_be_clickable((By.CLASS_NAME, "rating-ranking-view")), 10
        )
        logger.info("Клик по селекту сортировки отзывов")
        # Наводимся и кликаем
        ActionChains(browser.driver).move_to_element(order_select_element).click(
            order_select_element
        ).perform()
        # Ждем открытие попапа
        browser.wait_for_condition(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "rating-ranking-view__popup")
            )
        )
        # Получаем все опшины селекта
        options = browser.driver.find_elements(
            By.CLASS_NAME, "rating-ranking-view__popup-line"
        )
        # Выбираем рандомный опшн
        random_option = random.choice(options)
        logger.info("Клик по опшину в сортировке отзывов")
        browser.driver.execute_script("arguments[0].click();", random_option)
        time.sleep(5)

    except Exception as e:
        logger.error(f"Не удалось найти или нажать на кнопку отзывов: {e}")
        raise

    logger.success("Отзывы просмотрены")


def perform_target_action(browser: Browser):
    logger.info("Выполняем целевое действие")
    actions = [
        (click_whatsapp_link, "Переход на WhatsApp выполнен"),
        (click_telegram_link, "Переход на Telegram выполнен"),
        (click_website_link, "Переход на сайт выполнен"),
    ]
    for action, success_message in actions:
        if action(browser):
            logger.success(success_message)
            return_to_yandex_map_after_target_action(browser)
            return
    logger.critical("Не удалось перейти ни по одной ссылке")


def return_to_yandex_map_after_target_action(browser: Browser):
    # Запоминаем текущую вкладку
    original_window = browser.driver.current_window_handle
    # Находим новую вкладку и переключаемся на неё
    new_window = browser.driver.window_handles[-1]
    browser.driver.switch_to.window(new_window)
    time.sleep(5)  # Ожидание, чтобы убедиться, что страница загрузилась
    browser.driver.close()
    browser.driver.switch_to.window(original_window)


def click_telegram_link(browser: Browser):
    try:
        button = browser.wait_for_condition(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[aria-label="Соцсети, telegram"]')
            ),
            5,
        )
        # По ссылкам надо кликать так
        browser.driver.execute_script("arguments[0].click();", button)
        return True
    except Exception:
        logger.warning("Кнопка Telegram не найдена")
        return False


def click_whatsapp_link(browser: Browser):
    try:
        button = browser.wait_for_condition(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[aria-label="Соцсети, whatsapp"]')
            ),
            5,
        )
        browser.driver.execute_script("arguments[0].click();", button)
        return True
    except Exception:
        logger.warning("Кнопка WhatsApp не найдена")
        return False


def click_website_link(browser: Browser):
    try:
        button = browser.wait_for_condition(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".action-button-view._type_web")
            ),
            5,
        )
        browser.driver.execute_script("arguments[0].click();", button)
        return True
    except Exception:
        logger.warning("Кнопка сайта не найдена")
        return False
