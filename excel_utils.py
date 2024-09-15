import os
import shutil
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
from loguru import logger


def create_backup(file_name):
    """Создает резервную копию файла с указанием даты"""
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file_name = f"{file_name}_backup_{current_date}.xlsx"
    shutil.copy(file_name, backup_file_name)
    logger.info(f"Создана резервная копия файла: {backup_file_name}")


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
    
    if os.path.exists(file_name):
        create_backup(file_name)

    # Если файл не существует, создаем новую таблицу
    if not os.path.exists(file_name):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{current_month:02}.{current_year}"

        # Устанавливаем заголовки столбцов
        headers = ["Название заведения", "Запрос", "Частота"]

        # Генерация заголовков с датами на каждый день месяца
        for day in range(1, days_in_month + 1):
            date_str = f"{day:02}.{current_month:02}.{current_year}"
            headers.append(date_str)

        ws.append(headers)

        # Заполняем строками для каждого заведения и запроса
        row_index = 2  # Начинаем с первой строки после заголовков

        for establishment in establishments_data:
            establishment_id = establishment["id"]
            queries = establishment["queries"]

            for query in queries:
                row = [establishment_id, query, ""]  # Название заведения и запрос

                # Пустые значения для всех дней месяца
                row.extend([""] * days_in_month)
                ws.append(row)

                row_index += 1

        # Устанавливаем ширину колонок
        ws.column_dimensions["A"].width = 30  # Ширина колонки с названием заведения
        ws.column_dimensions["B"].width = 25  # Ширина колонки с запросом
        ws.column_dimensions["C"].width = 8  # Ширина колонки с частотой
        for col in range(
            4, len(headers) + 1
        ):  # Колонки с датами начинаются с колонки D (индекс 4)
            col_letter = get_column_letter(col)
            ws.column_dimensions[col_letter].width = (
                10  # Устанавливаем ширину колонок с датами
            )

        # Добавляем формулу SUM для столбца частот
        last_data_col = get_column_letter(len(headers))
        for row in range(2, row_index):
            ws.cell(row=row, column=3).value = f"=SUM(D{row}:{last_data_col}{row})"

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
        )  # Индекс колонки сегодняшнего дня
    else:
        # Если сегодня не в заголовках, добавляем его
        headers.append(today_str)
        today_col_index = len(headers)
        ws.cell(row=1, column=today_col_index, value=today_str)

    # Проверка существующих заведений в Excel (включая запросы)
    existing_rows = {
        (ws.cell(row=row, column=1).value, ws.cell(row=row, column=2).value): row
        for row in range(2, ws.max_row + 1)
    }

    # Добавляем новые строки для каждого запроса заведения, которых нет в существующей таблице
    for establishment in establishments_data:
        establishment_id = establishment["id"]
        queries = establishment["queries"]

        for query in queries:
            establishment_query_name = (establishment_id, query)

            if establishment_query_name not in existing_rows:
                logger.info(
                    f"Добавление нового заведения '{establishment_query_name[0]}' с запросом '{establishment_query_name[1]}' в отчет."
                )

                row = [establishment_id, query, ""]  # Название заведения и запрос

                # Пустые значения для всех дней месяца
                row.extend([""] * days_in_month)
                ws.append(row)

                # Обновляем карту существующих заведений и запросов
                existing_rows[establishment_query_name] = ws.max_row

    # Обновляем данные за сегодняшний день для существующих заведений и запросов
    for establishment in establishments_data:
        establishment_id = establishment["id"]
        queries = establishment["queries"]

        for query in queries:
            establishment_query_name = (establishment_id, query)
            row_index = existing_rows.get(establishment_query_name)

            if row_index is None:
                continue

            # Обновляем количество обработок за сегодняшний день
            if (
                today_str in establishment_dates
                and establishment_id in establishment_dates[today_str]
            ):
                query_count = (
                    establishment_dates[today_str]
                    .get(establishment_id, {})
                    .get(query, 0)
                )
                current_value = ws.cell(row=row_index, column=today_col_index).value

                # Если ячейка пустая или содержит нечисловое значение, инициализируем её
                if current_value is None or not isinstance(current_value, (int, float)):
                    ws.cell(row=row_index, column=today_col_index).value = query_count
                else:
                    ws.cell(row_index, column=today_col_index).value += query_count

    # Пересчитываем формулы SUM после обновления данных
    last_data_col = get_column_letter(len(headers))
    for row in range(2, ws.max_row + 1):
        ws.cell(row=row, column=3).value = f"=SUM(D{row}:{last_data_col}{row})"

    # Сохраняем изменения в файле
    wb.save(file_name)
    logger.info(f"Excel файл '{file_name}' успешно обновлен.")

    return file_name
