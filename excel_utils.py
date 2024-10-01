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


def create_or_update_excel_report(establishments_data, search_rankings_by_date):
    """
    Создает или обновляет Excel-отчет по заведениям.

    establishments_data: Список заведений и запросов
    search_rankings_by_date: Данные о позициях и частоте запросов за каждый день
    """
    print(search_rankings_by_date)
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
        wb.remove(wb.active)  # Удаляем автоматически созданный лист
        logger.info(f"Создан новый Excel файл '{file_name}' для текущего месяца.")
    else:
        wb = openpyxl.load_workbook(file_name)

    # Проходим по каждому заведению
    for establishment in establishments_data:
        establishment_id = establishment["id"]
        queries = establishment["queries"]

        # Проверяем, существует ли лист для заведения, если нет — создаем
        if establishment_id not in wb.sheetnames:
            ws = wb.create_sheet(title=establishment_id)

            # Устанавливаем заголовки столбцов
            headers = ["Запрос", "Частота"]
            for day in range(1, days_in_month + 1):
                date_str = f"{day:02}.{current_month:02}.{current_year}"
                headers.append(date_str)

            ws.append(headers)

            # Устанавливаем ширину колонок
            ws.column_dimensions["A"].width = 30  # Запрос
            ws.column_dimensions["B"].width = 10  # Частота
            for col in range(3, len(headers) + 1):  # Колонки с датами
                col_letter = get_column_letter(col)
                ws.column_dimensions[col_letter].width = 10
        else:
            ws = wb[establishment_id]

        # Проверка существующих запросов в Excel
        existing_queries = {
            ws.cell(row=row, column=1).value: row for row in range(2, ws.max_row + 1)
        }

        for query in queries:
            row_index = existing_queries.get(query)

            if row_index is None:
                # Добавляем новый запрос
                row_index = ws.max_row + 1
                ws.append([query, 0] + [""] * days_in_month)

            # Обновляем частоту запросов
            total_frequency = 0

            # Обновляем позиции по дням
            for date_str, search_info in search_rankings_by_date.items():
                if (
                    establishment_id in search_info
                    and query in search_info[establishment_id]
                ):
                    position_data = search_info[establishment_id][query]

                    # Извлекаем частоту и позицию
                    frequency = position_data[
                        "frequency"
                    ]  # Извлекаем значение frequency
                    position = position_data["position"]  # Извлекаем значение positions

                    day = int(date_str.split(".")[0])
                    col_index = 2 + day  # Колонка для соответствующего дня

                    print(ws.cell(row=row_index, column=col_index).value)
                    # Если позиция не пуста, обновляем ячейку
                    if (
                        ws.cell(row=row_index, column=col_index).value == None
                        or ws.cell(row=row_index, column=col_index).value == ""
                        or position < ws.cell(row=row_index, column=col_index).value
                    ):
                        ws.cell(row=row_index, column=col_index).value = position

                    # Добавляем частоту запросов за этот день
                    total_frequency += frequency  # Убедитесь, что это целое число

            # Обновляем общую частоту в столбце "Частота", если она еще не была установлена
            if ws.cell(row=row_index, column=2).value == 0:
                ws.cell(row=row_index, column=2).value = total_frequency
            else:
                ws.cell(
                    row=row_index, column=2
                ).value += total_frequency  # Увеличиваем частоту

    # Сохраняем изменения в файле
    wb.save(file_name)
    logger.info(f"Excel файл '{file_name}' успешно обновлен.")

    return file_name
