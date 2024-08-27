from loguru import logger
from run_application import run_application
from setup_logger import setup_dev_logger
from notifier import Notifier
# import time
# import schedule

@logger.catch
def main():
    setup_dev_logger()
    run_application()
    
    # Проверка отправки уведомлений
    # notifier = Notifier()
    # schedule.every(5).seconds.do(notifier.send_status_notification)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

if __name__ == '__main__':
    main()