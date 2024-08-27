import time
from loguru import logger
from browser_manager import initialize_browser
from config import SECOND_URL, START_URL

def run_application():
    logger.info('Старт')
    logger.info('Получение данных для входа в яндекс')
    
    logger.success('Данных для входа в яндекс получены')
    
    logger.info('Запуск браузера')
    browser = initialize_browser()
    
    try:
        browser.get(START_URL)
        browser.get(SECOND_URL)
        time.sleep(10)  # Подождем 10 секунд для наблюдения
    finally:
        browser.quit()