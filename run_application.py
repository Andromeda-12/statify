import time
from datetime import datetime
from loguru import logger
from browser import Browser
from config import APPLICATION_RUN_TIME, IS_DEV
from establishments_data import establishments_data
from establishments_logic import get_max_repeats, process_establishments
from excel_utils import create_or_update_excel_report
from notifier import Notifier
from yandex_login import login_to_yandex_account


def run_application(notifier: Notifier):
    logger.info("Старт")
    browser = Browser()

    # Инициализация словаря для отслеживания количества успешных обработок
    final_status = {
        establishment["id"]: {
            query: {
                "frequency": 0,
                "positions": float('inf'),
            }
            for query in establishment["queries"]
        }
        for establishment in establishments_data
    }

    try:
        max_repeats = get_max_repeats(establishments_data)

        for repetition_number in range(0, max_repeats):
            # Запуск браузера и вход в аккаунт
            login_to_yandex_account(browser)
            # Обработка заведения
            process_establishments(
                browser, establishments_data, repetition_number, final_status
            )
            browser.close_browser()
            if not IS_DEV:
                wait_time = 4800
                # Ждем какое-то время между каждой итерацией
                logger.info(f"Ждем {wait_time} секунд")
                time.sleep(wait_time)

    except Exception as e:
        logger.error(f"Ошибка в процессе выполнения: {e}")
    finally:
        if browser.is_open:
            browser.close_browser()

        log_report(establishments_data, final_status)

        if not IS_DEV:
            today = datetime.now().strftime("%d.%m.%Y")
            # Даты обработок заведений (сохранение позиций и частоты)
            search_rankings_by_date = {}

            # Инициализируем запись для текущей даты
            if today not in search_rankings_by_date:
                search_rankings_by_date[today] = {}

            # Проходим по заведениям и записываем данные
            for establishment in establishments_data:
                establishment_id = establishment["id"]

                # Создаем запись для каждого заведения
                if establishment_id not in search_rankings_by_date[today]:
                    search_rankings_by_date[today][establishment_id] = {}

                # Копируем данные по запросам из `final_status`
                for query, count in final_status[establishment_id].items():
                    search_rankings_by_date[today][establishment_id][query] = {
                        "position": count,  # Позиция запроса
                        "frequency": count,  # Частота запроса
                    }

            # Создание или обновление Excel-файла
            file_name = create_or_update_excel_report(
                establishments_data, search_rankings_by_date
            )

            # Отправка файла через notifier
            notifier.send_file(file_name)

            logger.info(f"Следующий запуск запланирован на {APPLICATION_RUN_TIME}")


def log_report(establishments_data, final_status):
    for establishment in establishments_data:
        establishment_id = establishment["id"]
        repeats_required = establishment["repeats"]
        total_successful_repeats = sum(
            query_info["frequency"]
            for query_info in final_status.get(establishment_id, {}).values()
        )

        if total_successful_repeats == repeats_required:
            logger.success(
                f"Заведение '{establishment_id}' успешно обработано {total_successful_repeats}/{repeats_required} раз(а)"
            )
        else:
            logger.critical(
                f"Заведение '{establishment_id}' не было обработано {repeats_required} раз(а). "
                f"Успешные обработки: {total_successful_repeats}/{repeats_required}. "
                f"Запросы: {', '.join(establishment['queries'])}, "
                f"Координаты: {establishment['coordinates']['latitude']}, {establishment['coordinates']['longitude']}"
            )
