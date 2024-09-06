from loguru import logger
from browser import Browser
from establishments_data import establishments_data
from establishments_logic import get_max_repeats, process_establishments
from helpers import declension
from yandex_login import login_to_yandex_account


def run_application():
    logger.info("Старт")
    browser = Browser()

    # Инициализация словаря для отслеживания количества успешных обработок
    final_status = {establishment["name"]: 0 for establishment in establishments_data}

    try:
        max_repeats = get_max_repeats(establishments_data)

        for repetition_number in range(0, max_repeats):
            # Запуск браузера и вход в аккаунт
            login_to_yandex_account(browser)
            # Обработка заведения
            process_establishments(
                browser, establishments_data, repetition_number, final_status
            )

    except Exception as e:
        logger.error(f"Ошибка в процессе выполнения: {e}")
    finally:
        if browser.is_open:
            browser.close_browser()

        for establishment in establishments_data:
            name = establishment["name"]
            repeats_required = establishment["repeats"]

            if final_status[name] == repeats_required:
                logger.success(
                    f"Заведение '{name}' успешно обработано {final_status[name]}/{repeats_required} {declension(final_status[name], 'раз', 'раза', 'раз')}"
                )
            else:
                logger.critical(
                    f"Заведение '{name}' не было обработано {repeats_required} {declension(repeats_required, 'раз', 'раза', 'раз')}. "
                    f"Успешные обработки: {final_status[name]}/{repeats_required}. "
                    f"Ниша: {establishment['niche']}, Координаты: {establishment['coordinates']}"
                )
