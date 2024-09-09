import random
import time
from loguru import logger
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.common.action_chains import ActionChains
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
        if self.driver and not self.is_open:
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
            logger.warning(f"Условие не было выполнено в течение {wait_time} секунд")
            raise

    def scroll_to(self, element: WebElement):
        """
        Прокрутка до элемента
        """
        self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", element)

    def move_to_element(self, element: WebElement):
        # Прокручиваем страницу до элемента
        self.scroll_to(element)
        # Получаем размеры элемента
        element_size = element.size
        # Определяем максимальные смещения
        max_offset_x = min(5, element_size["width"] / 2)
        max_offset_y = min(5, element_size["height"] / 2)
        # Генерируем случайные смещения в пределах указанных значений
        offset_x = random.randint(-max_offset_x, max_offset_x)
        offset_y = random.randint(-max_offset_y, max_offset_y)
        # Выполняем перемещение
        ActionChains(self.driver).move_to_element_with_offset(
            element, offset_x, offset_y
        ).perform()
        time.sleep(0.5)

    def move_to_element_and_click(self, element: WebElement):
        # Прокручиваем страницу до элемента
        self.scroll_to(element)
        # Получаем размеры элемента
        element_size = element.size
        # Определяем максимальные смещения
        max_offset_x = min(5, element_size["width"] / 2)
        max_offset_y = min(5, element_size["height"] / 2)
        # Генерируем случайные смещения в пределах указанных значений
        offset_x = random.randint(-max_offset_x, max_offset_x)
        offset_y = random.randint(-max_offset_y, max_offset_y)
        # Выполняем перемещение и клик
        ActionChains(self.driver).move_to_element_with_offset(
            element, offset_x, offset_y
        ).click().perform()
        time.sleep(0.5)
