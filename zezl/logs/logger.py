#
# Источник https://habr.com/ru/post/513966/
#

import logging
from logging.handlers import RotatingFileHandler

# блокируем логирование записей с модулей telegram и telegram.ext
from setup.data import LOG_FILE, APP_NAME
from subprocess import run, PIPE
# from shlex import quote as shlex_quote

try:
    from debug.remote_data import REMOTE_ACCESS_CMD
    ACCESS_REMOTE = True
except ImportError:
    ACCESS_REMOTE = False

# logging.getLogger("telegram").addHandler(logging.NullHandler())
# logging.getLogger("telegram.ext").addHandler(logging.NullHandler())

# запрещаем логирования из следующих модулей
logging.getLogger("telegram").propagate = False
logging.getLogger("apscheduler").propagate = False

# file_log = logging.FileHandler(LOG_FILE)

log_begin = "[%(levelname)s]" if ACCESS_REMOTE else "[%(asctime)s] [%(levelname)s] "
log_format = f'{log_begin} zezl -> %(filename)s::%(funcName)s [%(lineno)d] - "%(message)s"'
date_format = '%d-%m-%Y %H:%M:%S'


def get_file_handler():
    size_Mb = 1024 * 1024 * 1
    backup_count = 3
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=size_Mb, backupCount=backup_count)
    # file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    # file_handler.setLevel(logging.DEBUG)
    return file_handler


def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    # stream_handler.setLevel(logging.DEBUG)
    return stream_handler


def get_logger(name):
    # удаляем предыдущие логи при перезапуске пакета
    cmd = f"rm -f {LOG_FILE}*"
    run(args=cmd, stdout=PIPE, text=True, shell=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = get_stream_handler() if ACCESS_REMOTE else get_file_handler()
    logger.addHandler(handler)
    return logger


zlog = get_logger(APP_NAME)

