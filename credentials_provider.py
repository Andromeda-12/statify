import time
from typing import Callable, TypedDict
import requests
from abc import ABC, abstractmethod
from loguru import logger
from config import (
    ACCOUNT_PASSWORD,
    TEST_ACCOUNT_PASSWORD,
    TEST_ACCOUNT_USERNAME,
    API_365SMS_KEY,
)


class Credentials(TypedDict):
    login: str
    password: str
    activation_id: str


class CredentialsProvider(ABC):
    @abstractmethod
    def get_credentials(self) -> Credentials:
        """Метод для получения данных для входа"""
        pass

    @abstractmethod
    def get_sms_code(
        self, activation_id: str, retry_action: Callable[[], None]
    ) -> str | None:
        """
        Метод для получения кода активации.

        :param activation_id: ID активации, полученный при покупке номера
        :return: Код активации, если он получен, иначе None
        """
        pass


class SMS365CredentialsProvider(CredentialsProvider):
    def __init__(self):
        self.get_credentials_wait_time = 5
        self.sms_waiting_time = (
            90  # Время ожидания в секундах, за которое должно прийти смс
        )
        self.total_sms_waiting_time = (
            185  # Общее время ожидания в секундах, за которое должно прийти смс для этого номера
        )
        # Две попытки по 90 секунд, если за эти попытки не пришло смс, через 5 секунд отменяем вход через этот номер

    def get_credentials(self) -> Credentials:
        logger.info("Покупка номера на 365sms")

        # Бесконечный цикл для получения номера
        while True:
            try:
                # Запрос на получение номера
                response = requests.get(
                    f"https://365sms.ru/stubs/handler_api.php?api_key={API_365SMS_KEY}&action=getNumber&service=ya&operator=any&country=0"
                )
                # Проверка статуса ответа
                if response.status_code == 200:
                    # Ответ сервиса в виде строки
                    result = response.text.strip()

                    if result.startswith("ACCESS_NUMBER"):
                        # Разбиваем строку по ":"
                        _, activation_id, number = result.split(":")
                        logger.success(
                            f"Номер получен: {number}, ID активации: {activation_id}"
                        )
                        return {
                            "login": number,
                            "password": ACCOUNT_PASSWORD,
                            "activation_id": activation_id,
                        }

                    elif result == "NO_NUMBERS":
                        logger.info(
                            f"NO_NUMBERS: Нет номеров с заданными параметрами, повторная попытка через {self.get_credentials_wait_time} секунд..."
                        )
                        # Ждем указанное количество секунд перед повторной попыткой
                        time.sleep(self.get_credentials_wait_time)
                        continue

                    elif result == "NO_BALANCE":
                        logger.error(f"NO_BALANCE: Недостаточно средств на аккаунте.")
                        raise Exception("NO_BALANCE: Недостаточно средств на аккаунте.")

                    elif result == "WRONG_SERVICE":
                        logger.error(f"WRONG_SERVICE: Неверный идентификатор сервиса.")
                        raise Exception(
                            "WRONG_SERVICE: Неверный идентификатор сервиса."
                        )

                    else:
                        logger.error(f"Неизвестный ответ от сервиса: {result}")
                        raise Exception(f"Неизвестный ответ от сервиса: {result}")
                else:
                    error_message = f"Ошибка при запросе к сервису 365sms: {response.status_code}, сообщение: {response.text}"
                    logger.error(error_message)
                    raise Exception(error_message)

            except requests.RequestException as e:
                error_message = f"Ошибка сети при обращении к 365sms: {e}"
                logger.error(error_message)
                raise Exception(error_message)

    def get_sms_code(
        self, activation_id: str, retry_action: Callable[[], None]
    ) -> str | None:
        start_time = time.time()
        while True:
            try:
                # СМС уже отправлено, ожидаем
                time.sleep(self.sms_waiting_time)
                # Запрос на получение статуса
                response = requests.get(
                    f"https://365sms.ru/stubs/handler_api.php?api_key={API_365SMS_KEY}&action=getStatus&id={activation_id}"
                )

                if response.status_code == 200:
                    result = response.text.strip()

                    if result.startswith("STATUS_OK"):
                        _, code = result.split(":")
                        logger.success(f"Код активации получен: {code}")
                        return code

                    elif result == "STATUS_WAIT_CODE":
                        logger.info(
                            f"STATUS_WAIT_CODE: Ожидание получения кода, повторная попытка через {self.sms_waiting_time} секунд"
                        )
                        # Нажатие на кнопку повторного запроса
                        retry_action()

                    else:
                        logger.error(
                            f"Неизвестный ответ от сервиса при запросе кода: {result}"
                        )
                        raise Exception(
                            f"Неизвестный ответ от сервиса при запросе кода: {result}"
                        )

                else:
                    error_message = f"Ошибка при запросе статуса: {response.status_code}, сообщение: {response.text}"
                    logger.error(error_message)
                    raise Exception(error_message)

                # Проверка времени выполнения
                elapsed_time = time.time() - start_time
                if elapsed_time > self.total_sms_waiting_time:
                    logger.error(
                        f"Не удалось получить код активации на текущий номер за {self.total_sms_waiting_time} секунд"
                    )
                    return None

            except requests.RequestException as e:
                error_message = f"Ошибка сети при запросе статуса: {e}"
                logger.error(error_message)
                raise Exception(error_message)


class DevCredentialsProvider(CredentialsProvider):
    def get_credentials(self) -> Credentials:
        logger.info("Получение данных для входа из конфигурации для разработки")
        return {
            "login": TEST_ACCOUNT_USERNAME,
            "password": TEST_ACCOUNT_PASSWORD,
            "activation_id": "IS_DEV",
        }

    def get_sms_code(self, activation_id, retry_action) -> str | None:
        logger.info("Введите код активации, полученный на телефон: ")
        sms_code = input("Код активации: ").strip()
        if sms_code:
            logger.success(f"Код активации получен: {sms_code}")
            return sms_code
        else:
            logger.info("Код активации не был введен")
            return None
