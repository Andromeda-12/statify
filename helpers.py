import re


def declension(number, singular, few, plural):
    """
    Склоняет слово в зависимости от числа и предоставленных окончаний

    :param number: Число, к которому нужно склонить слово
    :param singular: Окончание для единственного числа (например, "стол")
    :param few: Окончание для чисел 2-4 (например, "стола")
    :param plural: Окончание для множественного числа (например, "столов")
    :return: Слово в нужной форме.
    """
    if number % 10 == 1 and number % 100 != 11:
        return singular
    elif number % 10 in (2, 3, 4) and not (number % 100 in (12, 13, 14)):
        return few
    else:
        return plural


def parse_partial_address(partial_address: str):
    """
    Парсит частичный адрес для извлечения улицы/проспекта и номера дома

    :param partial_address: Частичный адрес с улицей и номером дома (например, "Гурьянова, 30")
    :return: Кортеж (улица, номер дома)
    """
    # Ищем улицу и номер дома в адресе
    match = re.match(r"(.+?),\s*(\d+[а-яА-Я]?)", partial_address)
    if match:
        street, house_number = match.groups()
        return street.strip(), house_number.strip()
    return None, None


def is_address_match(full_address: str, partial_address: str) -> bool:
    """
    Проверяет, содержатся ли улица и номер дома из partial_address в full_address

    :param full_address: Полный адрес (например, "ул. Гурьянова, 30, Москва, этаж 2")
    :param partial_address: Частичный адрес с улицей и номером дома (например, "Гурьянова, 30")
    :return: True, если в full_address есть улица и номер дома из partial_address, иначе False
    """
    # Парсим частичный адрес
    street, house_number = parse_partial_address(partial_address)
    # Если не удалось распарсить частичный адрес, возвращаем False
    if not street or not house_number:
        return False
    # Удаляем лишние пробелы и приводим полный адрес к нижнему регистру
    full_address = full_address.lower().strip()
    # Проверяем наличие улицы в полном адресе
    if street.lower() not in full_address:
        return False
    # Проверяем наличие номера дома в полном адресе
    if house_number.lower() not in full_address:
        return False
    return True
