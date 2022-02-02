import logging

server_logger = logging.getLogger('server_log')


class Port:
    """
    Класс - дескриптор для номера порта.
    Позволяет использовать только порты с 1023 по 65536.
    При попытке установить неподходящий номер порта генерирует исключение.
    """

    def __set__(self, instance, value: int):
        if not 1024 <= value <= 65535:
            text = f'Попытка запуска с некорректным номером ' \
                   f'порта {value}. Допустимы адреса с 1024 до 65535.'
            server_logger.critical(text)
            raise TypeError('Некорректный номер порта')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
