from loguru import logger
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.chrome.service import Service
from config import EDGE_DRIVER_PATH

def initialize_browser():
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    service = Service(EDGE_DRIVER_PATH)
    
    try:
        return webdriver.Edge(service=service, options=options)
    except Exception as e:
        logger.error('Ошибка при запуске браузера: {e}', e=e)
    