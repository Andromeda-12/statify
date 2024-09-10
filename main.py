import functools
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
    scheduled_run_application = functools.partial(run_application, notifier)
    schedule.every().day.at(APPLICATION_RUN_TIME).do(scheduled_run_application)
    logger.info(f"Установлен старт на {APPLICATION_RUN_TIME}")

    # Отправка уведомления каждый день
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
    notifier = Notifier()
    run_application(notifier)

    # Проверка отправки уведомлений
    # schedule.every(5).seconds.do(notifier.send_status_notification)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)


if __name__ == "__main__":
    if IS_DEV:
        dev_main()
    else:
        main()
