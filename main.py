import time
import schedule
from loguru import logger
from config import APPLICATION_RUN_TIME, IS_DEV, SEND_STATUS_NOTIFICATION_TIME
from run_application import run_application
from setup_logger import setup_logger
from notifier import Notifier
from dev_main import main as dev_main


@logger.catch(level="CRITICAL")
def main():
    logger.info("Запуск")
    notifier = Notifier()
    setup_logger(notifier)

    # Запуск каждый день в определенное время
    schedule.every().day.at(APPLICATION_RUN_TIME).do(run_application)
    logger.info("Установлен старт на {time}", time=APPLICATION_RUN_TIME)

    # Отправка уведомления каждые два дня
    schedule.every().day.at(SEND_STATUS_NOTIFICATION_TIME).do(
        notifier.send_status_notification
    )

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    if IS_DEV:
        dev_main()
    else:
        main()
