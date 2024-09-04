import time
import schedule
from loguru import logger
from config import APPLICATION_RUN_TIME, IS_DEV, SEND_STATUS_NOTIFICATION_TIME
from run_application import run_application
from setup_logger import setup_dev_logger, setup_logger
from notifier import Notifier


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


@logger.catch
def dev_main():
    setup_dev_logger()
    logger.info("Запуск в режиме разработки")
    run_application()

    # Проверка отправки уведомлений
    # notifier = Notifier()
    # schedule.every(5).seconds.do(notifier.send_status_notification)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)


if __name__ == "__main__":
    if IS_DEV:
        dev_main()
    else:
        main()
