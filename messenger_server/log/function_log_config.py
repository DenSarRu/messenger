import logging
import os

function_log = logging.getLogger('func_log')
function_log.setLevel(logging.DEBUG)

# строка формата сообщения
string_format = '[%(asctime)s] [%(levelname)-10s] [%(module)-8s] > %(message)s'
# строка формата времени
datefmt = '%Y-%m-%d %H:%M:%S'

try:
    os.mkdir('log')
except FileExistsError:
    pass
finally:
    function_file_handler = logging.FileHandler('log/function.log')

# создаем форматтер
file_format = logging.Formatter(fmt=string_format, datefmt=datefmt)
function_file_handler.setFormatter(file_format)
function_log.addHandler(function_file_handler)

if __name__ == '__main__':
    function_log.critical('some critical unresolved error!')
    function_log.info('tell someone about this')
    function_log.warning('another error')
