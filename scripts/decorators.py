from functools import wraps
import inspect
from log.function_log_config import function_log


def log(func):
    @wraps(func)
    def call(*args, **kwargs):
        res = func(*args, **kwargs)
        function_log.debug('Функция "{}" вызвана из функции "{}"'.format(func.__name__, inspect.stack()[1][3]))
        # function_log.debug('Функция "{}", вернула: {}'.format(func.__name__, res))
        return res

    return call
