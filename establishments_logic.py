import random
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from browser import Browser
from config import (
    MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET,
    MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS,
    MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
    MAX_ZOOM_TIMES,
)
from establishment_interaction import (
    interact_with_establishment,
    interact_with_single_target_establishment,
    interact_with_target_establishment,
)
from establishments_scraping import get_establishments, get_target_establishment_index
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def process_establishment_logic(
    browser: Browser,
    establishment: list,
    attempt_number: int,
    max_attempts: int,
    repeat_number: int,
    total_repeats: int,
    final_status: dict,
):
    """Выполнить логику для одного заведения"""
    target_establishment_id = establishment["id"]
    target_establishment_name = establishment["name"]
    target_establishment_queries = establishment["queries"]
    # Выбираем случайную строку из массива
    target_establishment_query = random.choice(target_establishment_queries)
    target_establishment_coordinates = establishment["coordinates"]
    target_establishment_address = establishment["address"]
    target_establishment_unique_case = establishment.get("unique_case")
    target_establishment_action_order = establishment.get("action_order")

    latitude = target_establishment_coordinates.get("latitude")
    longitude = target_establishment_coordinates.get("longitude")
    coordinates_string = f"{latitude}, {longitude}"
    logger.info(
        f"Обработка заведения: {target_establishment_id}, запрос: {target_establishment_query}, координаты {coordinates_string}"
    )
    logger.info(
        f"повтор: {repeat_number + 1}/{total_repeats}, попытка: {attempt_number + 1}/{max_attempts}"
    )

    get_target_establishment_attempt = 0
    target_establishment_index = -1
    establishments = []

    while get_target_establishment_attempt < MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS:
        try:
            input_coordinates(browser, target_establishment_coordinates)
            if not target_establishment_unique_case:
                input_query_and_search(browser, target_establishment_query)

                zoom_times = min(get_target_establishment_attempt + 1, MAX_ZOOM_TIMES)

                for _ in range(zoom_times):
                    zoom_in(browser)
            else:
                search_url = transform_yandex_maps_url(
                    browser.driver.current_url, target_establishment_query
                )
                browser.driver.get(search_url)
                time.sleep(5)
                zoom_out(browser)
                time.sleep(2)
                zoom_in(browser)
                time.sleep(2)

            establishments = get_establishments(browser)

            # Ситуация, когда рядом нет больше заведений по такому запросу и сразу же открывается целевое заведение
            if (
                not establishments
                and get_target_establishment_attempt + 1
                == MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS
            ):
                try:
                    logger.info(
                        f"Проверка, что по запросу '{target_establishment_query}' сразу было найдено целевое заведение '{target_establishment_id}'"
                    )

                    title = browser.driver.find_element(
                        By.CLASS_NAME, "card-title-view__title-link"
                    ).text

                    if (
                        title.lower().strip()
                        == target_establishment_name.lower().strip()
                    ):
                        logger.info(
                            f"По запросу '{target_establishment_query}' сразу было найдено целевое заведение '{target_establishment_id}'"
                        )
                        logger.info(
                            "_______________________________________________________"
                        )
                        logger.info(
                            f"Взаимодействие с целевым заведением '{target_establishment_id}'"
                        )

                        interact_with_single_target_establishment(browser, target_establishment_action_order)

                        logger.success(
                            f"Выполнено целевое действие для заведения '{target_establishment_id}'"
                        )
                        logger.info(
                            "_______________________________________________________"
                        )

                        final_status[target_establishment_id][
                            target_establishment_query
                        ]["frequency"] += 1

                        if (
                            target_establishment_index + 1
                            < final_status[target_establishment_id][
                                target_establishment_query
                            ]["positions"]
                        ):
                            final_status[target_establishment_id][
                                target_establishment_query
                            ]["positions"] = (target_establishment_index + 1)

                        logger.success(
                            f"Частота и позиция для заведения '{target_establishment_id}' по запросу '{target_establishment_query}' обновлены, частота: {final_status[target_establishment_id][target_establishment_query]['frequency']}, позиция: {final_status[target_establishment_id][target_establishment_query]['positions']}"
                        )

                        return

                except Exception as e:
                    logger.error(
                        f"Ошибка при попытке обработать заведение '{target_establishment_id}' по запросу '{target_establishment_query}': {e}"
                    )
                    break

            if not establishments:
                logger.warning(
                    f"Список заведений пуст при попытке обработать заведение '{target_establishment_id}' на попытке {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS}. Перезагружаем страницу и пробуем снова"
                )
                get_target_establishment_attempt += 1
                browser.driver.refresh()
                time.sleep(5)
                continue

            logger.info(
                f"Попытка {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS} получения целевого заведений"
            )

            target_establishment_index = get_target_establishment_index(
                establishments,
                target_establishment_name,
                target_establishment_address,
            )

            if (
                target_establishment_index == -1
                and get_target_establishment_attempt
                == MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS
            ):
                logger.warning(
                    f"Целевое заведение '{target_establishment_id}' не найдено на попытке {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS}"
                )
                break

            if target_establishment_index == -1:
                logger.warning(
                    f"Целевое заведение '{target_establishment_id}' не найдено на попытке {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS}. Перезагружаем страницу и пробуем снова"
                )
                get_target_establishment_attempt += 1
                browser.driver.refresh()
                time.sleep(5)
                continue

            logger.success(
                f"Целевое заведение '{target_establishment_id}' найдено по запросу '{target_establishment_query}' на индексе {target_establishment_index + 1} на попытке {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS}"
            )
            break
        except Exception as e:
            get_target_establishment_attempt += 1
            logger.warning(
                f"Ошибка при попытке найти целевое заведение на попытке {get_target_establishment_attempt + 1}/{MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS}, перезагружаем страницу и пробуем снова. Ошибка: {e}"
            )
            browser.driver.refresh()
            time.sleep(5)

    if target_establishment_index == -1:
        logger.error(
            f"Не удалось получить целевое заведение '{target_establishment_id}' после {MAX_GET_TARGET_ESTABLISHMENTS_ATTEMPTS} попыток"
        )
        raise Exception(f"Не удалось получить целевое заведение")

    try:
        # Взаимодействие с несколькими заведениями до целевого заведения
        interactions_count = 0
        for establishment_index, establishment in enumerate(establishments):
            # Прерываем цикл, если достигнуто максимальное количество взаимодействий
            if interactions_count >= MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET:
                break
            # Пропускаем целевое заведение
            if establishment_index == target_establishment_index:
                continue

            try:
                title_element = establishment.find_element(
                    By.CLASS_NAME, "search-business-snippet-view__title"
                )
                title = title_element.text
                logger.info(
                    f"Взаимодействие с заведением '{title}' для сравнения {interactions_count + 1}/{MAX_BROWSED_ESTABLISHMENTS_BEFORE_TARGET}"
                )
                interact_with_establishment(browser, establishment)
                interactions_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при взаимодействии с заведением на индексе {establishment_index}: {e}"
                )

        logger.success("Заведения перед целевым заведением просмотрены")

        target_establishment = establishments[target_establishment_index]

        logger.info("_______________________________________________________")
        logger.info(f"Взаимодействие с целевым заведением '{target_establishment_id}'")

        interact_with_target_establishment(browser, target_establishment, target_establishment_action_order)

        logger.success(
            f"Выполнено целевое действие для заведения '{target_establishment_id}'"
        )
        logger.info("_______________________________________________________")

        final_status[target_establishment_id][target_establishment_query][
            "frequency"
        ] += 1

        if (
            target_establishment_index + 1
            < final_status[target_establishment_id][target_establishment_query][
                "positions"
            ]
        ):
            final_status[target_establishment_id][target_establishment_query][
                "positions"
            ] = (target_establishment_index + 1)

        logger.success(
            f"Частота и позиция для заведения '{target_establishment_id}' по запросу '{target_establishment_query}' обновлены, частота: {final_status[target_establishment_id][target_establishment_query]['frequency']}, позиция: {final_status[target_establishment_id][target_establishment_query]['positions']}"
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке заведения: {e}")
        raise


def process_establishments(
    browser: Browser,
    establishments_data: list,
    repetition_number: int,
    final_status: dict,
):
    # Отслеживание успешности обработки каждого заведения
    establishment_status = {
        establishment["id"]: False
        for establishment in establishments_data
        if repetition_number < establishment["repeats"]
    }
    attempts = {establishment["id"]: 0 for establishment in establishments_data}

    while should_continue_processing(
        establishments_data,
        establishment_status,
        attempts,
        MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
    ):
        for establishment in establishments_data:
            establishment_id = establishment["id"]

            if (
                establishment_id in establishment_status
                and establishment_status[establishment_id]
            ):
                continue  # Пропускаем заведения, которые уже обработаны

            total_establishment_repeats = establishment["repeats"]

            if repetition_number < total_establishment_repeats:
                try:
                    attempt_number = attempts[establishment_id]
                    # Выполняем логику для текущего заведения
                    process_establishment_logic(
                        browser,
                        establishment,
                        attempt_number,
                        MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS,
                        repetition_number,  # Текущий номер повтора, начиная с 1
                        total_establishment_repeats,
                        final_status,  # Передаем final_status для обновления
                    )

                    # Если логика выполнилась успешно, отмечаем заведение как обработанное
                    establishment_status[establishment_id] = True
                    logger.success(
                        f"Заведение {establishment['id']} успешно обработано"
                    )
                    logger.info(
                        "________________________________________________________________________________________________________"
                    )

                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке заведения {establishment['id']}: {e}"
                    )
                    attempts[establishment_id] += 1
                    if (
                        attempts[establishment_id]
                        >= MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS
                    ):
                        latitude = establishment["coordinates"].get("latitude")
                        longitude = establishment["coordinates"].get("longitude")
                        coordinates_string = f"{latitude}, {longitude}"
                        logger.critical(
                            f"""Не удалось обработать заведение {establishment['id']} после {MAX_PROCESS_ESTABLISHMENTS_ATTEMPTS} попыток.
                            Запросы: {', '.join(establishment['queries'])}, 
                            Координаты: {coordinates_string}"""
                        )
                        logger.info(
                            "________________________________________________________________________________________________________"
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
        establishment_id = establishment["id"]
        # Проверяем, есть ли заведение в словарях establishment_status и attempts
        if establishment_id in establishment_status and establishment_id in attempts:
            # Если статус заведения False и количество попыток меньше максимума, продолжаем цикл
            if (
                not establishment_status[establishment_id]
                and attempts[establishment_id] < max_attempts
            ):
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
        browser.move_to_element_and_click(search_input)
        # Очищаем инпут
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE * 500)
        time.sleep(2)
        # Вводим координаты
        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")
        coordinates_string = f"{latitude}, {longitude}"
        search_input.send_keys(coordinates_string)
        search_input.send_keys(Keys.ENTER)
        # Ждем некоторое время, чтобы карта загрузилась
        time.sleep(5)
        # Очищаем введенные координаты с помощью BACKSPACE
        search_input.send_keys(Keys.BACKSPACE * 200)
        time.sleep(2)
        logger.info(f"Координаты {coordinates_string} введены")

    except NoSuchElementException:
        logger.error(
            f"Не удалось найти инпут для поиска мест и адресов, {browser.driver.current_url}"
        )
        raise
    except Exception as e:
        logger.error(f"Ошибка при вводе координат, {browser.driver.current_url}: {e}")
        raise


def input_query_and_search(browser: Browser, query: str):
    """
    Вводит нишу заведения в инпут поиска на карте и выполняет поиск
    """
    try:
        # Находим инпут для поиска мест и адресов
        search_input = browser.driver.find_element(
            By.XPATH, '//input[@placeholder="Поиск мест и адресов"]'
        )
        browser.move_to_element_and_click(search_input)
        # Очищаем инпут
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE * 500)
        time.sleep(2)
        # Вводим нишу заведения
        search_input.send_keys(query)
        # Находим кнопку "Найти" и нажимаем её
        search_button = browser.driver.find_element(
            By.XPATH, '//button[@aria-label="Найти"]'
        )
        search_button.click()
        # Ждем некоторое время, чтобы результаты поиска загрузились
        time.sleep(5)
        # Очищаем инпут
        search_input.send_keys(Keys.BACKSPACE * 200)
        time.sleep(2)
        # Инпут все еще в фокусе, убираем фокус
        search_input.send_keys(Keys.ESCAPE)
        logger.info(f"Запрос '{query}' введен, поиск выполнен успешно")

    except NoSuchElementException:
        logger.error("Не удалось найти инпут или кнопку для поиска")
        raise

    except TimeoutException:
        logger.error("Превышено время ожидания загрузки результатов поиска")
        raise

    except Exception as e:
        logger.error(f"Произошла ошибка при вводе ниши и выполнении поиска: {e}")
        raise


def zoom_in(browser: Browser):
    """
    Находит кнопку приближения и нажимает на нее
    """
    try:
        zoom_in_button = browser.driver.find_element(
            By.XPATH, '//button[@aria-label="Приблизить"]'
        )
        browser.move_to_element_and_click(zoom_in_button)
        logger.info("Кнопка 'Приблизить' нажата")
        time.sleep(1.5)
    except NoSuchElementException:
        logger.error("Кнопка 'Приблизить' не найдена на странице")
    except TimeoutException:
        logger.error("Превышено время ожидания кнопки 'Приблизить'")
    except Exception as e:
        logger.error(f"Произошла ошибка при попытке нажать на кнопку 'Приблизить': {e}")


def zoom_out(browser: Browser):
    """
    Находит кнопку отдаления и нажимает на нее
    """
    try:
        zoom_out_button = browser.driver.find_element(
            By.XPATH, '//button[@aria-label="Отдалить"]'
        )
        browser.move_to_element_and_click(zoom_out_button)
        logger.info("Кнопка 'Отдалить' нажата")
        time.sleep(1.5)
    except NoSuchElementException:
        logger.error("Кнопка 'Отдалить' не найдена на странице")
    except TimeoutException:
        logger.error("Превышено время ожидания кнопки 'Отдалить'")
    except Exception as e:
        logger.error(f"Произошла ошибка при попытке нажать на кнопку 'Отдалить': {e}")


def transform_yandex_maps_url(original_url, query):
    """
    Преобразует исходную ссылку на Яндекс.Карты с координатами в ссылку с поисковым запросом.

    Args:
        original_url (str): Исходная ссылка на Яндекс.Карты.
        query (str): Запрос для поиска (например, "автосервис").

    Returns:
        str: Преобразованная ссылка с новым запросом.
    """
    # Парсим исходную ссылку
    parsed_url = urlparse(original_url)

    # Извлекаем параметры запроса
    query_params = parse_qs(parsed_url.query)

    # Ищем координаты в параметрах ll или sll
    ll = query_params.get("ll")
    sll = query_params.get("sll")

    # Если координаты есть в параметре ll, используем их, иначе берем sll
    coordinates = ll[0] if ll else (sll[0] if sll else None)

    if not coordinates:
        raise ValueError("Координаты не найдены в URL")

    # Извлекаем часть пути, которая указывает на регион и город
    path_parts = parsed_url.path.split("/")
    region_and_city = "/".join(path_parts[2:4])

    # Устанавливаем новый путь URL с поисковым запросом
    new_path = f"/maps/{region_and_city}/search/{query}/"

    # Обновляем параметры запроса
    new_query_params = {
        "ll": coordinates,
        "sll": coordinates,
        "z": 20,  # Задаем масштаб
    }

    # Строим новый URL
    new_query_string = urlencode(new_query_params, doseq=True)
    new_url = urlunparse(
        (
            parsed_url.scheme,  # схема (https)
            parsed_url.netloc,  # домен (yandex.ru)
            new_path,  # новый путь с запросом
            "",  # параметры
            new_query_string,  # новый строка параметров
            "",  # фрагмент
        )
    )

    return new_url
