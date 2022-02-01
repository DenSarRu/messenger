"""
Модуль создания логгера:
 - создание именованного логгера;
 - задание формата для логов:
    "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
 - указание файла для логгирования;
 - настройка ежедневной ротации лог-файлов.
"""
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler


server_loger = logging.getLogger('server_log')
server_loger.setLevel(logging.DEBUG)

# строка формата сообщения
string_format = '[%(asctime)s] [%(levelname)-10s] [%(module)-8s] [%(funcName)-30s] > %(message)s'
# строка формата времени
datefmt = '%Y-%m-%d %H:%M:%S'

try:
    os.mkdir('log')
except FileExistsError:
    pass
finally:
    server_file_handler = TimedRotatingFileHandler('log/messenger_server.log',
                                                   when="midnight",
                                                   backupCount=7,
                                                   encoding='utf-8'
                                                   )

# создаем форматтер
file_format = logging.Formatter(fmt=string_format, datefmt=datefmt)
server_file_handler.setFormatter(file_format)
server_file_handler.setLevel(logging.WARNING)

server_stream_handler = logging.StreamHandler(sys.stderr)
# создаем форматтер
stream_format = logging.Formatter(fmt=string_format, datefmt=datefmt)
server_stream_handler.setFormatter(stream_format)
server_stream_handler.setLevel(logging.DEBUG)

server_loger.addHandler(server_stream_handler)
server_loger.addHandler(server_file_handler)

if __name__ == '__main__':
    server_loger.critical('some messenger_server critical unresolved error!')
    server_loger.info('tell someone this info')
    server_loger.warning('another error with messenger_server')
