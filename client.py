"""
    Класс клиента:
        ● сформировать presence-сообщение;
        ● отправить сообщение серверу;
        ● получить ответ сервера;
        ● разобрать сообщение сервера;
        ● параметры командной строки скрипта messenger_client.py <addr> [<port>]:
            ○ addr — ip-адрес сервера;
            ○ port — tcp-порт на сервере, по умолчанию 7777.
"""
import json
import logging
import socket
import sys
import threading
import time

from decorators import log
from descriptors import Port
from metaclasses import ClientVerifier
from utils import parse, get_message, send_message, load_configs
from log import client_log_config

# Инициализация клиентского логера
client_logger = logging.getLogger('client_log')
CONFIGS = {}
socket_lock = threading.Lock()


class Client(threading.Thread, metaclass=ClientVerifier):
    """Основной_класс_клиентского_модуля, отвечает_за_связь_с_сервером"""

    __port = Port()

    def __init__(self, address, port):
        threading.Thread.__init__(self)
        self.__logger = client_logger
        self.__address = address
        self.__port = port
        self.__CONFIGS = load_configs(is_server=False)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.__user_name = None
        # self.__password = None

        # self.__sock.settimeout(5)
        super().__init__()

    @log
    def create_presence_message(self, account_name):
        """
            Формирование сообщения о присутствии
            :param account_name: строка псевдонима
            :return: словарь ответа о присутствии клиента
            """
        if not isinstance(account_name, str):
            self.__logger.warning(f"Ошибка указания имени пользователя {account_name}")
            raise TypeError
        if len(account_name) > 25:
            self.__logger.warning("create_message: Username Too Long")
            raise ValueError
        presence_message = {
            self.__CONFIGS.get('ACTION'): self.__CONFIGS.get('PRESENCE'),
            self.__CONFIGS.get('TIME'): time.time(),
            self.__CONFIGS.get('USER'): {
                self.__CONFIGS.get('ACCOUNT_NAME'): account_name
            }
        }
        self.__logger.debug(f'Сформировано {self.__CONFIGS.get("PRESENCE")} '
                            f'сообщение для пользователя {account_name}')
        return presence_message

    @log
    def create_exit_message(self, account_name):
        """
        Формирование сообщения о выходе
        :param account_name: строка псевдонима
        :return: словарь ответа о выходе клиента
        """
        exit_message = {
            self.__CONFIGS.get('ACTION'): self.__CONFIGS.get('EXIT'),
            self.__CONFIGS.get('TIME'): time.time(),
            self.__CONFIGS.get('USER'): {
                self.__CONFIGS.get('ACCOUNT_NAME'): account_name
            }
        }
        self.__logger.debug(f'Сформировано {self.__CONFIGS.get("EXIT")} '
                            f'сообщение для пользователя {account_name}')
        return exit_message

    @log
    def user_action(self, user_name):
        """
        Обработчик поступающих команд от клиента
        :param sock: клиентский сокет
        :param user_name: имя текущего клиента
        :return:
        """
        while True:
            command = input('Введите "message" для приема и отправки сообщения, "exit" для выхода: ')
            if command == 'message':
                self.write_messages(self.__sock, user_name)
            elif command == 'exit':
                send_message(self.__sock, self.create_exit_message(user_name), self.__CONFIGS)
                self.__logger.info('Завершение работы по команде пользователя')
                print('*** Завершение работы ***')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробуйте снова. \n'
                      'Введите "message" для приема и отправки сообщения, "exit" для выхода: ')

    @log
    def write_messages(self, sock, account_name):
        """
            Формирование и отправка на сервер сообщения клиента
            :param sock: клиентский сокет
            :param account_name: имя отправителя
            :return message_dict: словарь сообщения клиента
        """
        receiver_name = input('Введите получателя сообщения -->  ')
        message_text = input('Введите сообщение --> ')

        message = {
            self.__CONFIGS.get('ACTION'): 'msg',
            self.__CONFIGS.get('TIME'): time.time(),
            self.__CONFIGS.get('SENDER'): account_name,
            self.__CONFIGS.get('DESTINATION'): receiver_name,
            self.__CONFIGS.get('MESSAGE'): message_text
        }

        self.__logger.debug(f'Сформировано сообщение: {message}')

        self.__logger.debug("Попытка отправки сообщения...")
        try:
            send_message(sock, message, self.__CONFIGS)
            self.__logger.info(f'Отправлено сообщение для пользователя {receiver_name}')
        except Exception:
            self.__logger.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @log
    def message_from_server(self, user_name):
        self.__logger.debug(f'Разбор сообщения от сервера')
        while True:
            try:
                message = get_message(self.__sock, self.__CONFIGS)
                if self.__CONFIGS.get('RESPONSE') in message:
                    if message[self.__CONFIGS.get('RESPONSE')] == 200:
                        return '200 : OK'
                    elif message[self.__CONFIGS.get('RESPONSE')] == 400:
                        self.__logger.debug(f'Получено сообщение от сервера: {message["response"]} : {message["error"]}')
                        return f'400 : {message[self.__CONFIGS.get("ERROR")]}'
                elif self.__CONFIGS['ACTION'] in message and message[self.__CONFIGS['ACTION']] == 'msg' and \
                        self.__CONFIGS['SENDER'] in message and self.__CONFIGS['DESTINATION'] in message \
                        and self.__CONFIGS['MESSAGE'] in message and message[
                    self.__CONFIGS['DESTINATION']] == user_name:
                    print(f'\nПолучено сообщение от пользователя {message[self.__CONFIGS["SENDER"]]}: '
                          f'{message[self.__CONFIGS["MESSAGE"]]}')
                    self.__logger.info(f'Получено сообщение от пользователя {message[self.__CONFIGS["SENDER"]]}:'
                                       f' {message[self.__CONFIGS["MESSAGE"]]}')
                # Отключение от сервера
                elif message['action'] == 'quit':
                    break
                else:
                    self.__logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                self.__logger.critical('Потеряно соединение с сервером.')
                break

    @log
    def create_client_socket(self, user_name):
        """
        метод отвечающий за создание соединения с сервером
        :param user_name: имя пользователя
        :param address: адрес сервера
        :param port: порт, по которому происходит подключение. по умолчанию 7777
        :return:
        """

        # Соединяется с сервером
        self.__sock.connect((self.__address, self.__port))

        with socket_lock:
            # Формируем сообщение о присутствии
            presence_message = self.create_presence_message(user_name)

            # Отправляем сообщение о присутствии серверу
            send_message(self.__sock, presence_message, self.__CONFIGS)

            try:
                hanlded_response = self.message_from_server(user_name)
                if hanlded_response == "200 : OK":
                    self.__logger.info(f'Установлено соединение с сервером. Ответ сервера: {hanlded_response}')
                else:
                    raise ConnectionRefusedError
            except (ValueError, json.JSONDecodeError):
                self.__logger.error('Ошибка декодирования сообщения')
                sys.exit(1)
            except ConnectionRefusedError:
                self.__logger.critical(f'Не удалось подключиться к серверу {self.__address}:{self.__port}, '
                                       f'запрос на подключение отклонён. Причина: {hanlded_response}')
            else:
                # Запускает клиентский процесс приёма сообщений
                self.__logger.debug('** Запуск потока \'thread-1\' для приёма сообщений **')
                receiver = threading.Thread(target=self.message_from_server, args=(user_name,))
                receiver.daemon = True
                receiver.start()

                # Запускает отправку сообщений и взаимодействие с клиентом
                self.__logger.debug('** Запуск потока \'thread-2\' для отправки сообщений **')
                self.__logger.debug('** Процессы запущены **\n')
                user_interface = threading.Thread(target=self.user_action, args=(user_name,))
                user_interface.daemon = True
                user_interface.start()

                # Watchdog основной цикл, если один из потоков завершён,
                # то значит потеряно соединение или пользователь ввёл exit.
                # Поскольку все события обрабатываются в потоках,
                # достаточно завершить цикл.messenger_client
                while True:

                    time.sleep(1)
                    if user_interface.is_alive():
                        continue
                    break

    @log
    def run(self):
        self.__logger.info('Клиент запущен!!')
        client_name = input('Введите имя пользователя: ')
        self.__logger.info(f'Запущен клиент с парамертами: '
                           f'адрес сервера: {self.__address}, порт: {self.__port}, имя пользователя: {client_name}')
        self.create_client_socket(client_name)


if __name__ == "__main__":
    args = parse(is_server=False)
    client = Client(args.address, args.port)
    client.run()
