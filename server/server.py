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
from scripts.decorators import log
from scripts.descriptors import Port
from scripts.metaclasses import ServerVerifier
from scripts.utils import parse, get_message, send_message, load_configs
from .db.database import ServerStorage

# инициализация серверного логера
server_logger = logging.getLogger('server_log')
CONFIGS = {}


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, address, port, server_storage):
        self.__CONFIGS = load_configs()
        self.__logger = server_logger
        self.__storage = server_storage

        self.__logger.debug('Запуск сервера!')
        self.__address = address
        self.__port = port
        self.running = True
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
        if self.__CONFIGS.get('ACTION') in message \
                and message[self.__CONFIGS.get('ACTION')] == self.__CONFIGS.get('PRESENCE') \
                and self.__CONFIGS.get('TIME') in message:
            self.authorize_user(message, sock)
            return

        # формирует очередь сообщений
        elif self.__CONFIGS.get('ACTION') in message and message[self.__CONFIGS.get('ACTION')] == 'msg' and \
                self.__CONFIGS.get('SENDER') in message and self.__CONFIGS.get('DESTINATION') in message and \
                self.__CONFIGS.get('MESSAGE') in message and self.__CONFIGS.get('TIME') in message:
            self.__logger.debug('формирует очередь сообщений')
            self.all_messages.append(message)
            return

        # добавление пользователя
        elif self.__CONFIGS.get('ACTION') in message \
                and message[self.__CONFIGS.get('ACTION')] == 'add_contact' \
                and self.all_names[message['user']] == sock:
            self.__storage.add_contact(message['user'], message['contact_name'])
            self.__logger.debug(f"Для клиента {message['user']} добавлен контакт {message['contact_name']}")
            response = {
                "response": 202
            }
            send_message(sock, response, self.__CONFIGS)

        # удаление пользователя
        elif self.__CONFIGS.get('ACTION') in message \
                and message[self.__CONFIGS.get('ACTION')] == 'del_contact' \
                and self.all_names[message['user']] == sock:
            self.__storage.remove_contact(message['user'], message['contact_name'])
            self.__logger.debug(f"Для клиента {message['user']} удалён контакт {message['contact_name']}")
            response = {
                "response": 202
            }
            send_message(sock, response, self.__CONFIGS)

        # Получение списка контактов
        elif message['action'] == 'get_contacts':
            self.__logger.debug(f'Получен запрос списка контактов от пользователя {message["user_login"]}')
            names = self.__storage.get_contact_list(message['user_login'])
            response = {
                "response": 202,
                "alert": names
            }
            self.__logger.debug(f'Подготовлен список контактов: {names}')
            send_message(sock, response, self.__CONFIGS)

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
        for user in self.__storage.users_list():
            self.__storage.user_logout(user)
        while self.running:
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

    @log
    def remove_client_by_name(self, user_name: str):
        """
        Метод ищет клиента по имени и запускает для него метод удаления.
        :param user_name:
        :return:
        """
        sock = self.__name_socket.get(user_name)
        if sock:
            self.__remove_client(sock)

    @log
    def authorize_user(self, message, sock):
        """Метод реализующий авторизцию пользователей."""
        # авторизация
        user_name = message[self.__CONFIGS.get("USER")][self.__CONFIGS.get("ACCOUNT_NAME")]
        self.__logger.debug(f'Авторизация клиента: {user_name}')
        if user_name not in self.all_names.keys():
            self.all_names[user_name] = sock
            self.__storage.add_user(user_name)
            send_message(sock, {self.__CONFIGS.get('RESPONSE'): 200}, self.__CONFIGS)
            # print(self.__storage.get_user_by_name(message[self.__CONFIGS.get("USER")][self.__CONFIGS.get("ACCOUNT_NAME")]))
            self.__logger.info(
                f'Авторизован клиент: {user_name}')
        else:
            response = {
                self.__CONFIGS.get('RESPONSE'): 400,
                self.__CONFIGS.get('ERROR'): 'Имя пользователя уже занято.'
            }
            self.__logger.warning(
                f'Повторная попытка авторизации клиента: {user_name}!'
                f'Отказ. Имя пользователя уже занято.')
            send_message(sock, response, self.__CONFIGS)
            self.all_clients.remove(sock)
            sock.close()
        return


if __name__ == "__main__":
    args = parse()
    server = Server(args.address, args.port, ServerStorage())
    try:
        server.run()
    except Exception as e:
        server_logger.error('Exception: {}'.format(str(e)))
    server_logger.info("Server stopped")
