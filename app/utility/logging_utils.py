import graypy
import logging
from fastapi import BackgroundTasks
from config.config import settings




log = logging.getLogger('my_logger')
log.setLevel(logging.DEBUG)

log_mode = settings.log_mode

if log_mode == 'graylog':
    graylog_host = settings.graylog_host
    graylog_port = settings.graylog_port
    gelf_handler = graypy.GELFUDPHandler(graylog_host,graylog_port)
    # gelf_handler = graypy.GELFHTTPHandler(config['GRAYLOG_HOST'], config['GRAYLOG_PORT'])
    log.addHandler(gelf_handler)

elif log_mode == 'file':
    file_handler = logging.FileHandler('app.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

elif log_mode == 'console':
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)


def log_background(message: str, level: str = "info"):
    if level == "info":
        log.info(message)
    elif level == "error":
        log.error(message)
    elif level == "warning":
        log.warning(message)



def log_async(background_tasks: BackgroundTasks, message: str, level: str = "info", always_sync=False):
    if always_sync or not background_tasks:
        log_background(message, level)  # sync logging immediately
    else:
        background_tasks.add_task(log_background, message, level)  # async, runs after response

