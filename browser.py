from loguru import logger
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebElement
from selenium.common.exceptions import TimeoutException
from config import BROWSER_CONDITION_WAIT_TIME, EDGE_DRIVER_PATH


class Browser:
    def __init__(self):
        self.driver = None
        self.is_open = False
        self.options = Options()
        self._configure_options()

    def _configure_options(self):
        """Настройка опций для браузера"""
        # Игнорирование предупреждений сертификатов
        self.options.add_argument("--ignore-certificate-errors")
        # Запуск браузера на весь экран
        self.options.add_argument("--start-maximized")
        # Выключение логов браузера
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # Отключение определения браузера как вебдрайвер
        self.options.add_argument("--disable-blink-features=AutomationControlled")

    def start_browser(self):
        """Запуск браузера"""
        try:
            service = Service(EDGE_DRIVER_PATH)
            self.driver = webdriver.Edge(service=service, options=self.options)
            self.is_open = True
            logger.success("Браузер успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            self.driver = None

    def close_browser(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                self.is_open = False
                logger.success("Браузер успешно закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
        else:
            logger.warning("Браузер не был запущен или уже закрыт")

    def wait_for_condition(
        self, func, wait_time=BROWSER_CONDITION_WAIT_TIME
    ) -> WebElement:
        """
        Ожидание выполнения условия

        :param func: Функция ожидания, которая должна вернуть True, когда условие выполнено
        :return: Результат выполнения функции `func`, если условие выполнено
        :raises TimeoutException: Если условие не выполнено
        """
        try:
            return WebDriverWait(self.driver, wait_time).until(func)
        except TimeoutException:
            logger.error(f"Условие не было выполнено в течение {wait_time} секунд")
            raise

    def scroll_to(self, element: WebElement):
        """
        Прокрутка до элемента
        """
        self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", element)
