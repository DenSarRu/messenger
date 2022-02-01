""""
Класс сервера:
    ● принимает сообщение клиента;
    ● формирует ответ клиенту;
    ● отправляет ответ клиенту;
    ● имеет параметры командной строки:
        ○ -p <port> — TCP-порт для работы (по умолчанию использует 7777);
        ○ -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import logging
import select
import socket
import threading

from log import server_log_config
from decorators import log
from descriptors import Port
from utils import parse, get_message, send_message, load_configs
from metaclasses import ServerVerifier

# инициализация серверного логера
server_logger = logging.getLogger('server_log')
CONFIGS = {}


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, address, port):
        self.__CONFIGS = load_configs()
        self.__logger = server_logger

        self.__logger.debug('Запуск сервера!')
        self.__address = address
        self.__port = port
        # self.__sock = None
        self.listen_sockets = None
        # Список клиентов и очередь сообщений
        self.all_clients = []
        self.all_messages = []
        # Словарь зарегистрированных клиентов: ключ - имя пользователя, значение - сокет
        self.all_names = {}
        # Создает TCP-сокет сервера
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Связывает сокет с ip-адресом и портом сервера
        self.__sock.bind((self.__address, self.__port))
        # Запускает режим прослушивания
        self.__sock.listen(self.__CONFIGS.get('MAX_CONNECTIONS'))
        self.__sock.settimeout(0.5)  # Таймаут для операций с сокетом
        self.__logger.debug('Server socket created')
        super().__init__()

    # @log
    # def init_socket(self):

    # # Создает TCP-сокет сервера
    # self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # # Связывает сокет с ip-адресом и портом сервера
    # self.__sock.bind((self.__address, self.__port))
    # # Запускает режим прослушивания
    # self.__sock.listen(self.__CONFIGS.get('MAX_CONNECTIONS'))
    # self.__sock.settimeout(0.5)  # Таймаут для операций с сокетом
    # self.__logger.debug('Server socket created')

    @log
    def parse_client_msg(self, message, sock):
        """
            Обработчик сообщений клиентов
            :param message: словарь сообщения
            :param messages_list: список сообщений
            :param sock: клиентский сокет
            :param clients_list: список клиентских сокетов
            :param names: список зарегистрированных клиентов
            :return: словарь ответа
            """
        self.__logger.debug(f'Разбор сообщения от клиента: {message}')

        # возвращает сообщение о присутствии
        if self.__CONFIGS.get('ACTION') in message \
                and message[self.__CONFIGS.get('ACTION')] == self.__CONFIGS.get('PRESENCE') \
                and self.__CONFIGS.get('TIME') in message:

            # авторизация
            if message[self.__CONFIGS.get('USER')][self.__CONFIGS.get('ACCOUNT_NAME')] not in self.all_names.keys():
                self.all_names[message[self.__CONFIGS.get('USER')][self.__CONFIGS.get('ACCOUNT_NAME')]] = sock
                send_message(sock, {self.__CONFIGS.get('RESPONSE'): 200}, self.__CONFIGS)
                self.__logger.info(
                    f'Авторизован клиент: {message[self.__CONFIGS.get("USER")][self.__CONFIGS.get("ACCOUNT_NAME")]}')
            else:
                response = {
                    self.__CONFIGS.get('RESPONSE'): 400,
                    self.__CONFIGS.get('ERROR'): 'Имя пользователя уже занято.'
                }
                self.__logger.warning(
                    f'Повторная попытка авторизации клиента: {message[self.__CONFIGS.get("USER")][self.__CONFIGS.get("ACCOUNT_NAME")]}!'
                    f'Отказ. Имя пользователя уже занято.')
                send_message(sock, response, self.__CONFIGS)
                self.all_clients.remove(sock)
                sock.close()
            return

        # формирует очередь сообщений
        elif self.__CONFIGS.get('ACTION') in message and message[self.__CONFIGS.get('ACTION')] == 'msg' and \
                self.__CONFIGS.get('SENDER') in message and self.__CONFIGS.get('DESTINATION') in message and \
                self.__CONFIGS.get('MESSAGE') in message and self.__CONFIGS.get('TIME') in message:
            self.__logger.debug('формирует очередь сообщений')
            self.all_messages.append(message)
            return

        # выход клиента
        elif self.__CONFIGS.get('ACTION') in message and message[self.__CONFIGS.get('ACTION')] == 'exit' and \
                self.__CONFIGS.get('ACCOUNT_NAME') in message[self.__CONFIGS.get('USER')]:
            self.__logger.debug(
                f'выход клиента {message[self.__CONFIGS.get("USER")][self.__CONFIGS.get("ACCOUNT_NAME")]}')
            response = {
                "action": "quit"
            }
            send_message(sock, response, self.__CONFIGS)

            self.all_clients.remove(
                self.all_names[message[self.__CONFIGS.get('USER')][self.__CONFIGS.get('ACCOUNT_NAME')]])
            self.all_names[message[self.__CONFIGS.get('USER')][self.__CONFIGS.get('ACCOUNT_NAME')]].close()
            del self.all_names[message[self.__CONFIGS.get('USER')][self.__CONFIGS.get('ACCOUNT_NAME')]]
            return

        # возвращает сообщение об ошибке
        else:
            response = {
                self.__CONFIGS.get('RESPONSE'): 400,
                self.__CONFIGS.get('ERROR'): 'Bad Request',
            }
            send_message(sock, response, self.__CONFIGS)
            return

    @log
    def route_client_msg(self, message):
        """
        Адресная отправка сообщений.
        :param message: словарь сообщения
        :param names: список зарегистрированных клиентов
        :param clients: список слушающих клиентских сокетов
        :return:
        """
        if message[self.__CONFIGS.get('DESTINATION')] in self.all_names and self.all_names[
            message[self.__CONFIGS.get('DESTINATION')]] in self.listen_sockets:
            send_message(self.all_names[message[self.__CONFIGS.get('DESTINATION')]], message, self.__CONFIGS)
            self.__logger.info(f'Отправлено сообщение пользователю {message[self.__CONFIGS.get("DESTINATION")]} '
                               f'от пользователя {message[self.__CONFIGS.get("SENDER")]}.')
        elif message[self.__CONFIGS.get('DESTINATION')] in self.all_names and self.all_names[
            message[self.__CONFIGS.get('DESTINATION')]] not in self.listen_sockets:
            raise ConnectionError
        else:
            self.__logger.error(
                f'Пользователь {message[self.__CONFIGS.get("DESTINATION")]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    @log
    def run(self):
        # self.init_socket()

        while True:
            # Принимает запрос на соединение
            # Возвращает кортеж (новый TCP-сокет клиента, адрес клиента)
            try:
                client_tcp, client_address = self.__sock.accept()
            except OSError:
                pass
            else:
                self.__logger.info(f'Установлено соедение с клиентом {client_address}')
                client_tcp.settimeout(0)
                self.all_clients.append(client_tcp)

            r_clients = []
            w_clients = []
            errs = []

            # Запрашивает информацию о готовности к вводу, выводу и о наличии исключений для
            # группы дескрипторов сокетов
            try:
                if self.all_clients:
                    r_clients, self.listen_sockets, errs = select.select(self.all_clients,
                                                                         self.all_clients, [], 0)
            except OSError:
                pass

            # Чтение запросов из списка клиентов
            if r_clients:
                for r_sock in r_clients:
                    try:
                        self.parse_client_msg(get_message(r_sock, self.__CONFIGS), r_sock)
                    except Exception as ex:
                        self.__logger.error(f'Клиент отключился от сервера. '
                                            f'Тип исключения: {type(ex).__name__}, аргументы: {ex.args}')
                        self.all_clients.remove(r_sock)

            # Роутинг сообщений адресатам
            for msg in self.all_messages:
                try:
                    self.route_client_msg(msg)
                except Exception:
                    self.__logger.info(f'Связь с клиентом {msg[self.__CONFIGS.get("DESTINATION")]} была потеряна')
                    self.all_clients.remove(self.all_names[msg[self.__CONFIGS.get("DESTINATION")]])
                    del self.all_names[msg[self.__CONFIGS.get("DESTINATION")]]
            self.all_messages.clear()


if __name__ == "__main__":
    args = parse()
    server = Server(args.address, args.port)
    try:
        server.run()
    except Exception as e:
        server_logger.error('Exception: {}'.format(str(e)))
    server_logger.info("Server stopped")
