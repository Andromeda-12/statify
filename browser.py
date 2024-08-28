from loguru import logger
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from config import EDGE_DRIVER_PATH

class Browser:
    def __init__(self):
        self.driver = None
        self.options = Options()
        self._configure_options()

    def _configure_options(self):
        """Настройка опций для браузера."""
        # Игнорирование предупреждений сертификатов
        self.options.add_argument("--ignore-certificate-errors")
        # Запуск браузера на весь экран
        self.options.add_argument("--start-maximized")
        # Выключение логов браузера
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # Отключение определения браузера как вебдрайвер
        self.options.add_argument("--disable-blink-features=AutomationControlled")

    def start_browser(self):
        """Запуск браузера."""
        try:
            service = Service(EDGE_DRIVER_PATH)
            self.driver = webdriver.Edge(service=service, options=self.options)
            logger.success("Браузер успешно запущен.")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            self.driver = None

    def close_browser(self):
        """Закрытие браузера."""
        if self.driver:
            try:
                self.driver.quit()
                logger.success("Браузер успешно закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
        else:
            logger.warning("Браузер не был запущен или уже закрыт.")
            
    def wait_for_condition(self, func):
        """
        Ожидание выполнения условия в течение 60 секунд.
        
        :param func: Функция ожидания, которая должна вернуть True, когда условие выполнено.
        :return: Результат выполнения функции `func`, если условие выполнено в течение 60 секунд.
        :raises TimeoutException: Если условие не выполнено в течение 60 секунд.
        """
        try:
            return WebDriverWait(self.driver, 60).until(func)
        except TimeoutException:
            logger.error("Условие не было выполнено в течение 60 секунд.")
            raise
