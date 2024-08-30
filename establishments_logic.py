from loguru import logger

from browser import Browser


def get_max_repeats(establishments_data: list):
    """Получить максимальное значение repeat из данных заведений."""
    return max(establishment["repeats"] for establishment in establishments_data)


def process_establishment_logic(
    browser: Browser,
    establishment: list,
    attempt_number: int,
    repeat_number: int,
    total_repeats: int,
):
    """Выполнить логику для одного заведения."""
    name = establishment["name"]
    niche = establishment["niche"]
    coordinates = establishment["coordinates"]
    logger.info(f"Обработка заведения {name} ({niche}) с координатами {coordinates}")
    logger.info(
        f"повтор: {repeat_number + 1}, всего: {total_repeats}, попытка: {attempt_number + 1}"
    )
    # TODO: Логика для заведения


def process_establishments(
    browser: Browser, establishments_data: list, repetition_number: int, final_status: dict
):
    max_attempts = 5
    # Отслеживание успешности обработки каждого заведения
    establishment_status = {
        establishment["name"]: False for establishment in establishments_data if repetition_number < establishment["repeats"]
    }
    attempts = {establishment["name"]: 0 for establishment in establishments_data}
    
    while should_continue_processing(establishments_data, establishment_status, attempts, max_attempts):
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
                    if attempts[name] >= max_attempts:
                        logger.critical(
                            f"Не удалось обработать заведение {establishment['name']} после {max_attempts} попыток. "
                            f"Ниша {establishment["niche"]}. "
                            f"Координаты {establishment['coordinates']}"
                        )
    
    if all(establishment_status.values()):
        logger.success(f"Обработаны все заведения на повторении {repetition_number + 1}")
    else:
        unprocessed = [
            name for name, processed in establishment_status.items() if not processed
        ]
        logger.warning(
            f"Заведения обработаны на повторении {repetition_number + 1}. Не удалось обработать следующие заведения: {', '.join(unprocessed)}"
        )

def should_continue_processing(establishments_data, establishment_status, attempts, max_attempts):
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
