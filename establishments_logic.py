import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from browser import Browser
from config import (
    MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET,
    MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
)
from establishment_interaction import (
    interact_with_establishment,
    interact_with_target_establishment,
)
from establishments_scraping import get_establishments, get_target_establishment_index


def process_establishment_logic(
    browser: Browser,
    establishment: list,
    attempt_number: int,
    max_attempts: int,
    repeat_number: int,
    total_repeats: int,
):
    """Выполнить логику для одного заведения"""
    target_establishment_name = establishment["name"]
    target_establishment_niche = establishment["niche"]
    target_establishment_coordinates = establishment["coordinates"]
    target_establishment_address = establishment["address"]

    logger.info(
        f"Обработка заведения {target_establishment_name} ({target_establishment_niche}) с координатами {target_establishment_coordinates}"
    )
    logger.info(
        f"повтор: {repeat_number + 1}/{total_repeats}, попытка: {attempt_number + 1}/{max_attempts}"
    )

    try:
        input_coordinates(browser, target_establishment_coordinates)
        input_niche_and_search(browser, target_establishment_niche)

        establishments = get_establishments(browser)

        if not establishment:
            raise Exception("Список заведений пуст")

        target_index = get_target_establishment_index(
            browser,
            establishments,
            target_establishment_name,
            target_establishment_address,
        )

        if target_index == -1:
            raise Exception("Не удалось найти целевое заведение в списке заведений")

        interactions_count = 0
        for establishment_index, establishment in enumerate(establishments):
            if establishment_index == target_index:
                continue  # Пропускаем целевое заведение

            if interactions_count >= MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET:
                break  # Прерываем цикл, если достигнуто максимальное количество взаимодействий с заведениями

            try:
                logger.info(
                    f"Взаимодействие с заведением для сравнения {establishment_index}/{MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET}"
                )
                interact_with_establishment(browser, establishment)
                interactions_count += 1
            except Exception as e:
                # Не увеличиваем interactions_count, чтобы попробовать посмотреть другое заведение
                logger.error(
                    f"Ошибка при взаимодействии с заведением на индексе {establishment_index}: {e}"
                )

        logger.success("Заведения просмотрены")

        target_establishment = establishments[target_index]

        logger.info("____________________________________________")
        logger.info("Взаимодействие c целевым заведение")

        interact_with_target_establishment(browser, target_establishment)

        logger.success(
            f"Выполнено целевое действие для заведения '{target_establishment_name}'"
        )
        logger.info("____________________________________________")
    except:
        raise


def process_establishments(
    browser: Browser,
    establishments_data: list,
    repetition_number: int,
    final_status: dict,
):
    # Отслеживание успешности обработки каждого заведения
    establishment_status = {
        establishment["name"]: False
        for establishment in establishments_data
        if repetition_number < establishment["repeats"]
    }
    attempts = {establishment["name"]: 0 for establishment in establishments_data}

    while should_continue_processing(
        establishments_data,
        establishment_status,
        attempts,
        MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
    ):
        for establishment in establishments_data:
            name = establishment["name"]

            if name in establishment_status and establishment_status[name]:
                continue  # Пропускаем заведения, которые уже обработаны

            total_establishment_repeats = establishment["repeats"]

            if repetition_number < total_establishment_repeats:
                try:
                    attempt_number = attempts[name]
                    # Выполняем логику для текущего заведения
                    process_establishment_logic(
                        browser,
                        establishment,
                        attempt_number,
                        MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
                        repetition_number,  # Текущий номер повтора, начиная с 1
                        total_establishment_repeats,
                    )

                    # Если логика выполнилась успешно, отмечаем заведение как обработанное
                    establishment_status[name] = True
                    final_status[name] += 1
                    logger.success(
                        f"Заведение {establishment['name']} успешно обработано"
                    )

                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке заведения {establishment['name']}: {e}"
                    )
                    attempts[name] += 1
                    if attempts[name] >= MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS:
                        logger.critical(
                            f"""Не удалось обработать заведение {establishment['name']} после {MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS} попыток.
                            Ниша {establishment["niche"]}. "
                            Координаты {establishment['coordinates']}"""
                        )

    if all(establishment_status.values()):
        logger.success(
            f"Обработаны все заведения на повторении {repetition_number + 1}"
        )
    else:
        unprocessed = [
            name for name, processed in establishment_status.items() if not processed
        ]
        logger.warning(
            f"Заведения обработаны на повторении {repetition_number + 1}. Не удалось обработать следующие заведения: {', '.join(unprocessed)}"
        )


def get_max_repeats(establishments_data: list):
    """Получить максимальное значение repeat из данных заведений"""
    return max(establishment["repeats"] for establishment in establishments_data)


def should_continue_processing(
    establishments_data, establishment_status, attempts, max_attempts
):
    """
    Проверяет, нужно ли продолжать цикл обработки заведений
    """
    for establishment in establishments_data:
        name = establishment["name"]
        # Проверяем, есть ли заведение в словарях establishment_status и attempts
        if name in establishment_status and name in attempts:
            # Если статус заведения False и количество попыток меньше максимума, продолжаем цикл
            if not establishment_status[name] and attempts[name] < max_attempts:
                return True
    # Если не нашлось ни одного заведения, у которого можно продолжить попытки, завершаем цикл
    return False


def input_coordinates(browser: Browser, coordinates: dict):
    """
    Вводит координаты в инпут поиска на карте и ожидает загрузки карты
    """
    try:
        # Находим инпут для поиска мест и адресов
        search_input = browser.driver.find_element(
            By.XPATH, '//input[@placeholder="Поиск мест и адресов"]'
        )
        # Очищаем инпут
        search_input.send_keys(Keys.BACKSPACE * 500)
        # Вводим координаты
        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")
        coordinates_string = f"{latitude}, {longitude}"
        search_input.send_keys(coordinates_string)
        search_input.send_keys(Keys.ENTER)
        # Ждем некоторое время, чтобы карта загрузилась
        time.sleep(5)
        # Очищаем введенные координаты с помощью BACKSPACE
        search_input.send_keys(Keys.BACKSPACE * len(coordinates_string))
        logger.info(f"Координаты {coordinates_string} введены")

    except NoSuchElementException:
        logger.error("Не удалось найти инпут для поиска мест и адресов")
        raise
    except Exception as e:
        logger.error(f"Ошибка при вводе координат: {e}")
        raise


def input_niche_and_search(browser: Browser, niche: str):
    """
    Вводит нишу заведения в инпут поиска на карте и выполняет поиск
    """
    try:
        # Находим инпут для поиска мест и адресов
        search_input = browser.driver.find_element(
            By.XPATH, '//input[@placeholder="Поиск мест и адресов"]'
        )
        # Очищаем инпут
        search_input.send_keys(Keys.BACKSPACE * 500)
        # Вводим нишу заведения
        search_input.send_keys(niche)
        # Находим кнопку "Найти" и нажимаем её
        search_button = browser.driver.find_element(
            By.XPATH, '//button[@aria-label="Найти"]'
        )
        search_button.click()
        # Ждем некоторое время, чтобы результаты поиска загрузились
        time.sleep(5)
        # Очищаем инпут
        search_input.send_keys(Keys.BACKSPACE * len(niche))
        # Инпут все еще в фокусе, убираем фокус
        search_input.send_keys(Keys.ESCAPE)
        logger.info(f"Ниша '{niche}' введена, поиск выполнен успешно")

    except NoSuchElementException:
        logger.error("Не удалось найти инпут или кнопку для поиска")
        raise

    except TimeoutException:
        logger.error("Превышено время ожидания загрузки результатов поиска")
        raise

    except Exception as e:
        logger.error(f"Произошла ошибка при вводе ниши и выполнении поиска: {e}")
        raise
