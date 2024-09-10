import time
from datetime import datetime
from loguru import logger
from browser import Browser
from config import IS_DEV
from establishments_data import establishments_data
from establishments_logic import get_max_repeats, process_establishments
from excel_utils import create_or_update_excel_report
from helpers import declension
from notifier import Notifier
from yandex_login import login_to_yandex_account


def run_application(notifier: Notifier):
    logger.info("Старт")
    browser = Browser()

    # Инициализация словаря для отслеживания количества успешных обработок
    final_status = {
        establishment["id"]: {query: 0 for query in establishment["queries"]}
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
            if not IS_DEV:
                # Ждем какое-то время между каждой итерацией
                time.sleep(4800)

    except Exception as e:
        logger.error(f"Ошибка в процессе выполнения: {e}")
    finally:
        if browser.is_open:
            browser.close_browser()

        log_report(establishments_data, final_status)

        if IS_DEV:
            # Обновляем данные по обработкам независимо от успешности
            today = datetime.now().strftime(
                "%d.%m.%Y"
            )  # Текущая дата в формате дд.мм.гггг
            # Даты обработок
            establishment_dates = {}
            # Инициализируем запись для текущей даты, если её нет
            if today not in establishment_dates:
                establishment_dates[today] = {}

            for establishment in establishments_data:
                establishment_id = establishment["id"]
                # Инициализируем запись для заведения, если её нет
                if establishment_id not in establishment_dates[today]:
                    establishment_dates[today][establishment_id] = {}

                # Копируем данные по запросам из final_status для текущей даты
                for query, count in final_status[establishment_id].items():
                    establishment_dates[today][establishment_id][query] = count

            # Создание или обновление Excel файла
            file_name = create_or_update_excel_report(
                establishments_data, establishment_dates
            )
            notifier.send_file(file_name)


def log_report(establishments_data, final_status):
    for establishment in establishments_data:
        establishment_id = establishment["id"]
        repeats_required = establishment["repeats"]
        total_successful_repeats = sum(final_status[establishment_id].values())

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
