"""
Модуль создания логгера:
 - создание именованного логгера;
 - задание формата для логов:
    "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
 - указание файла для логгирования;
"""

import logging
import sys


client_log = logging.getLogger('client_log')
client_log.setLevel(logging.DEBUG)

# строка формата сообщения
string_format = '[%(asctime)s] [%(levelname)-10s] [%(module)-8s] [%(funcName)-30s] > %(message)s'
# строка формата времени
datefmt = '%Y-%m-%d %H:%M:%S'

client_file_handler = logging.FileHandler('log/client.log')
# создаем форматтер
file_format = logging.Formatter(fmt=string_format, datefmt=datefmt)
client_file_handler.setFormatter(file_format)
client_file_handler.setLevel(logging.WARNING)

client_stream_handler = logging.StreamHandler(sys.stderr)
stream_format = logging.Formatter(fmt=string_format, datefmt=datefmt)
client_stream_handler.setFormatter(stream_format)
client_stream_handler.setLevel(logging.DEBUG)

client_log.addHandler(client_stream_handler)
client_log.addHandler(client_file_handler)

if __name__ == '__main__':
    client_log.critical('some critical unresolved error!')
    client_log.info('tell someone about this')
    client_log.warning('another error')
