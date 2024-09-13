import random
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from browser import Browser
from config import MAX_BROWSE_ESTABLISHMENTS_REVIEWS_ITERATIONS


def interact_with_establishment(browser: Browser, establishment: WebElement):
    open_establishment_card(browser, establishment)
    check_modal_window(browser)
    set_arrow_buttons_display_none(browser)
    browse_establishment_photos(browser)
    browse_establishment_reviews_multiple_times(browser)


def interact_with_target_establishment(
    browser: Browser, target_establishment: WebElement
):
    interact_with_establishment(browser, target_establishment)
    open_establishment_overview(browser)
    perform_target_action(browser)


def check_modal_window(browser: Browser):
    try:
        browser.wait_for_condition(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dialog._fullscreen")), 5
        )
        logger.info("Появилось модальное окно, пытаемся его закрыть")
        close_button = browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.close-button[aria-label="Закрыть"]')
            ),
            5,  # Задаем время ожидания в секундах
        )
        browser.wait_for_condition(EC.element_to_be_clickable(close_button), 15)
        browser.move_to_element(close_button)
        browser.driver.execute_script("arguments[0].click();", close_button)
        logger.info("Модальное окно закрыто")
    except TimeoutException:
        logger.info("Модальное окно не появилось")
        pass
    except Exception as e:
        logger.error(
            f"Произошла ошибка при попытке найти или закрыть модальное окно: {e}"
        )


def open_establishment_card(browser: Browser, establishment: WebElement):
    try:
        browser.wait_for_condition(EC.element_to_be_clickable(establishment), 15)
        # Кликаем на заведение
        browser.move_to_element_and_click(establishment)
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
        time.sleep(5)
        browser.wait_for_condition(EC.element_to_be_clickable(overview_button), 15)
        logger.info('Клик по кнопке "Обзор"')
        browser.move_to_element_and_click(overview_button)
        time.sleep(5)
    except TimeoutException:
        logger.warning("Не удалось найти кнопку обзор или она не кликабельная")
        return
    except Exception as e:
        logger.error(f"Не удалось найти или нажать на кнопку обзор: {e}")
        time.sleep(3)
        raise


def browse_establishment_photos(browser: Browser):
    try:
        # Находим кнопку фотографий
        photos_button = browser.wait_for_condition(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div._name_gallery")),
            10,
        )
        browser.scroll_to(photos_button)
        time.sleep(3)
        browser.wait_for_condition(EC.element_to_be_clickable(photos_button), 15)
        logger.info("Клик по кнопке с фото")
        browser.move_to_element_and_click(photos_button)
        # Потому что не всегда кликается
        photos_button.click()
        time.sleep(3)
    except TimeoutException:
        logger.warning("Не удалось найти кнопку фотографий или она не кликабельная")
        return
    except Exception as e:
        logger.error(f"Ошибка при попытке найти кнопку фотографий: {e}")
        raise

    try:
        # Проверка наличия элемента с фото
        photo_element = browser.wait_for_condition(
            EC.presence_of_element_located((By.CLASS_NAME, "media-wrapper")), 10
        )
        browser.wait_for_condition(EC.element_to_be_clickable(photo_element), 15)
        browser.move_to_element_and_click(photo_element)
        logger.info("Клик по фото")
        time.sleep(3)
        close_button = browser.wait_for_condition(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".photos-player-view__button._type_close")
            ),
            10,
        )
        browser.wait_for_condition(EC.element_to_be_clickable(close_button), 15)
        browser.move_to_element_and_click(close_button)
        logger.info("Фото закрыто")
        time.sleep(3)
    except TimeoutException:
        logger.warning(
            "Элемент с фото не найден, или не получилось закрыть фото, или кнопка не кликабельная"
        )
        return
    except Exception as e:
        logger.warning(f"Ошибка при попытке посмотреть или закрыть фото: {e}")
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
        try:
            # Находим кнопку отзывов
            reviews_button = browser.wait_for_condition(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div._name_reviews")
                ),
                10,
            )
            browser.scroll_to(reviews_button)
            time.sleep(5)
            browser.wait_for_condition(EC.element_to_be_clickable(reviews_button), 15)
            browser.move_to_element_and_click(reviews_button)
            reviews_button.click()
            logger.info("Клик по отзывам")
            time.sleep(5)
        except TimeoutException:
            logger.warning("Не удалось найти кнопку отзывов или она не кликабельная")
            return
        except Exception as e:
            logger.error(f"Ошибка при попытке найти кнопку отзывов: {e}")
            raise

        try:
            # Находим селект выбора сортировки отзывов
            order_select_element = browser.wait_for_condition(
                EC.element_to_be_clickable((By.CLASS_NAME, "rating-ranking-view")), 20
            )
            logger.info("Клик по селекту сортировки отзывов")
            # Наводимся и кликаем
            browser.move_to_element_and_click(order_select_element)
            time.sleep(3)
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
            browser.move_to_element(random_option)
            browser.driver.execute_script("arguments[0].click();", random_option)
            time.sleep(5)

        except TimeoutException:
            logger.warning("Не удалось найти селект сортировки отзывов")
            return
        except Exception as e:
            logger.error(f"Ошибка при попытке найти селект сортировки отзывов: {e}")
            raise

        logger.success("Отзывы просмотрены")
    except:
        logger.warning("Отзывы не были просмотрены")
        raise


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
    raise Exception("Не удалось перейти ни по одной ссылке")


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
        browser.wait_for_condition(EC.element_to_be_clickable(button), 15)
        # По ссылкам надо кликать так
        browser.move_to_element_and_click(button)
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
        browser.wait_for_condition(EC.element_to_be_clickable(button), 15)
        browser.move_to_element_and_click(button)
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
        browser.wait_for_condition(EC.element_to_be_clickable(button), 15)
        browser.move_to_element_and_click(button)
        return True
    except Exception:
        logger.warning("Кнопка сайта не найдена")
        return False


def set_arrow_buttons_display_none(browser: Browser):
    try:
        prev_arrow = browser.driver.find_element(
            By.CSS_SELECTOR, ".carousel__arrow-wrapper._centered._prev._size_m"
        )
        next_arrow = browser.driver.find_element(
            By.CSS_SELECTOR, ".carousel__arrow-wrapper._centered._next._size_m"
        )
        browser.driver.execute_script(
            "arguments[0].style.display = 'none';", prev_arrow
        )
        browser.driver.execute_script(
            "arguments[0].style.display = 'none';", next_arrow
        )
    except:
        logger.error("Не удалось найти кнопки со стрелкой и скрыть их")
