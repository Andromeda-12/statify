import sys
from loguru import logger


def setup_logger(notifier):
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            }
        ]
    )
    # Отправка уведомлений об ошибках через ТГ бота
    logger.add(
        notifier.send_notification,
        format="Произошла ошибка\n\n{time:MMMM D, YYYY > HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="CRITICAL",
    )
    # Логирование в файл, новый файл создается каждый день в 9:00
    logger.add(
        "work.log",
        format="{time}:{level}:{message}",
        rotation="9:00",
        retention="30 days",
        compression="zip",
    )
    logger.info("Логгер настроен")


def setup_dev_logger():
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            }
        ]
    )
    logger.info("Логгер настроен")
