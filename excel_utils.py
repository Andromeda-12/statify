import os
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
from loguru import logger


def create_or_update_excel_report(establishments_data, establishment_dates):
    # Определяем текущий месяц и год
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    days_in_month = (
        (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).day
        if current_month != 12
        else 31
    )

    # Имя файла для текущего месяца
    file_name = f"Отчет_по_заведениям_{current_month:02}_{current_year}.xlsx"

    # Если файл не существует, создаем новую таблицу
    if not os.path.exists(file_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{current_month:02}.{current_year}"

        # Устанавливаем заголовки столбцов
        headers = ["Название заведения (Ниша)", "Частота"]

        # Генерация заголовков с датами на каждый день месяца
        for day in range(1, days_in_month + 1):
            date_str = f"{day:02}.{current_month:02}.{current_year}"
            headers.append(date_str)

        ws.append(headers)

        # Заполняем строками с пустыми значениями
        for row_index, establishment in enumerate(establishments_data, start=2):
            niche = establishment["niche"]
            name = establishment["name"]
            row = [f"{name} ({niche})"]  # Название заведения

            # Формула для подсчета частоты
            last_date_column = get_column_letter(len(headers))
            frequency_formula = f"=SUM(C{row_index}:{last_date_column}{row_index})"
            row.append(frequency_formula)

            # Пустые значения для всех дней месяца
            row.extend([""] * days_in_month)
            ws.append(row)

        # Устанавливаем ширину колонок
        ws.column_dimensions["A"].width = 50  # Ширина первой колонки
        for col in range(
            3, len(headers) + 1
        ):  # Колонки с датами начинаются с колонки C (индекс 3)
            col_letter = get_column_letter(col)
            ws.column_dimensions[col_letter].width = (
                10  # Устанавливаем ширину колонок с датами
            )

        wb.save(file_name)
        logger.info(f"Создан новый Excel файл '{file_name}' для текущего месяца.")

    # Открываем существующий файл для обновления
    wb = openpyxl.load_workbook(file_name)
    ws = wb.active

    # Получаем все заголовки в первой строке
    headers = [ws.cell(row=1, column=col).value for col in range(1, ws.max_column + 1)]

    # Ищем индекс столбца для сегодняшней даты
    today_str = current_date.strftime("%d.%m.%Y")
    if today_str in headers:
        today_col_index = (
            headers.index(today_str) + 1
        )  # Индекс колонки сегодняшнего дня (с учетом 1-based index в Excel)
    else:
        raise ValueError(f"Дата '{today_str}' не найдена в заголовках Excel файла.")

    # Проверка существующих заведений в Excel (даже если они были удалены из данных)
    existing_establishments = {
        ws.cell(row=row, column=1).value.split(" (")[0]: row
        for row in range(2, ws.max_row + 1)
    }

    # Добавляем новые заведения, которых нет в существующей таблице
    for establishment in establishments_data:
        name = establishment["name"]
        if name not in existing_establishments:
            logger.info(f"Добавление нового заведения '{name}' в отчет.")

            niche = establishment["niche"]
            row = [f"{name} ({niche})"]  # Название заведения

            # Формула для подсчета частоты
            last_date_column = get_column_letter(len(headers))
            frequency_formula = (
                f"=SUM(C{ws.max_row + 1}:{last_date_column}{ws.max_row + 1})"
            )
            row.append(frequency_formula)

            # Пустые значения для всех дней месяца
            row.extend([""] * days_in_month)
            ws.append(row)

            # Обновляем карту существующих заведений
            existing_establishments[name] = ws.max_row

    # Обновляем данные за сегодняшний день для существующих заведений
    for name, row_index in existing_establishments.items():
        # Если заведение больше не существует в актуальных данных, пропускаем обновление
        if name not in [est["name"] for est in establishments_data]:
            continue

        # Обновляем количество обработок за сегодняшний день
        if today_str in establishment_dates[name]:
            current_value = ws.cell(row=row_index, column=today_col_index).value

            # Если ячейка пустая или содержит нечисловое значение, инициализируем её
            if current_value is None or not isinstance(current_value, (int, float)):
                ws.cell(row=row_index, column=today_col_index).value = (
                    establishment_dates[name][today_str]
                )
            else:
                ws.cell(
                    row=row_index, column=today_col_index
                ).value += establishment_dates[name][today_str]

    # Сохраняем изменения в файле
    wb.save(file_name)
    logger.info(f"Excel файл '{file_name}' успешно обновлен.")

    return file_name
