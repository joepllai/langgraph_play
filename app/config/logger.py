import logging


class LoggerConfig:
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "app.log"
    LOG_MAX_BYTES = 1024
    LOG_BACKUP_COUNT = 3
