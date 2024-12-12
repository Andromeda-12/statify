import random
import time
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from config import BROWSER_CONDITION_WAIT_TIME, DRIVER_PATH
from selenium_stealth import stealth

# initializing a list with two User Agents
useragentarray = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
]


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
        # exclude the collection of enable-automation switches
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # Отключение определения браузера как вебдрайвер
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--headless")
        # adding argument to disable the AutomationControlled flag
        # turn-off userAutomationExtension
        self.options.add_experimental_option("useAutomationExtension", False)

    def start_browser(self):
        """Запуск браузера"""
        try:
            service = Service(executable_path='chromedriver.exe')
            self.driver = webdriver.Chrome(service=service, options=self.options)

            # changing the property of the navigator value for webdriver to undefined
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            for i in range(len(useragentarray)):
                # setting User Agent iteratively as Chrome 108 and 107
                self.driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride", {"userAgent": useragentarray[i]}
                )
                self.driver.get("https://httpbin.io/headers")

            stealth(
                self.driver,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36",
                languages=["ru-RU", "ru"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )

            self.is_open = True

            logger.success("Браузер успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            self.driver = None

    def close_browser(self):
        """Закрытие браузера"""
        if self.driver and self.is_open:
            try:
                self.driver.quit()
                self.is_open = False
                logger.success("Браузер успешно закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
        else:
            logger.warning("Браузер не был запущен или уже закрыт")

    def wait_for_condition(
        self, func, wait_time=BROWSER_CONDITION_WAIT_TIME, silent=False
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
            if not silent:
                logger.warning(
                    f"Условие не было выполнено в течение {wait_time} секунд"
                )
                raise

    def scroll_to(self, element: WebElement):
        """
        Прокрутка до элемента
        """
        self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", element)
        time.sleep(1)

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
        ActionChains(self.driver).scroll_to_element(
            element
        ).move_to_element_with_offset(element, offset_x, offset_y).perform()
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
        ActionChains(self.driver).scroll_to_element(
            element
        ).move_to_element_with_offset(element, offset_x, offset_y).click().perform()
        time.sleep(0.5)
