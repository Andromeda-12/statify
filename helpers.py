def declension(number, singular, few, plural):
    """
    Склоняет слово в зависимости от числа и предоставленных окончаний.

    :param number: Число, к которому нужно склонить слово.
    :param singular: Окончание для единственного числа (например, "стол").
    :param few: Окончание для чисел 2-4 (например, "стола").
    :param plural: Окончание для множественного числа (например, "столов").
    :return: Слово в нужной форме.
    """
    if number % 10 == 1 and number % 100 != 11:
        return singular
    elif number % 10 in (2, 3, 4) and not (number % 100 in (12, 13, 14)):
        return few
    else:
        return plural
