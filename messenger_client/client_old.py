"""
    Функции клиента:
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

from messenger_client.decorators import log
from messenger_server.utils import parse, load_configs, send_message, get_message

# Инициализация клиентского логера
client_logger = logging.getLogger('client_log')
CONFIGS = {}


@log
def create_presence_message(account_name, CONFIGS):
    """
        Формирование сообщения о присутствии
        :param account_name: строка псевдонима
        :return: словарь ответа о присутствии клиента
        """
    if not isinstance(account_name, str):
        client_logger.warning(f"Ошибка указания имени пользователя {account_name}")
        raise TypeError
    if len(account_name) > 25:
        client_logger.warning("create_message: Username Too Long")
        raise ValueError
    presence_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): account_name
        }
    }
    client_logger.debug(f'Сформировано {CONFIGS.get("PRESENCE")} '
                        f'сообщение для пользователя {account_name}')
    return presence_message


@log
def create_exit_message(account_name, CONFIGS):
    """
    Формирование сообщения о выходе
    :param account_name: строка псевдонима
    :return: словарь ответа о выходе клиента
    """
    exit_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('EXIT'),
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): account_name
        }
    }
    client_logger.debug(f'Сформировано {CONFIGS.get("EXIT")} '
                        f'сообщение для пользователя {account_name}')
    return exit_message


# @log
# def handle_response(message, user_name, CONFIGS):
#     """
#     Обработчик поступающих сообщений
#     :param message: принятое сообщение
#     :param user_name: имя текущего клиента
#     :return:
#     """
#     # если приветственное сообщение
#     if CONFIGS.get('RESPONSE') in message:
#         if message[CONFIGS.get('RESPONSE')] == 200:
#             return '200 : OK'
#         elif message[CONFIGS.get('RESPONSE')] == 400:
#             client_logger.debug(f'Получено сообщение от сервера: {message["response"]} {message["error"]}')
#             return f'400 : {message[CONFIGS.get("ERROR")]}'
#
#     # сообщение от другого клиента
#     elif message['action'] == 'msg' and message[CONFIGS.get('DESTINATION')] == user_name:
#         client_logger.info(
#             f'Получено сообщение от пользователя {message[CONFIGS.get("SENDER")]} --> {message[CONFIGS.get("MESSAGE")]}')
#         return f'{message[CONFIGS.get("SENDER")]} --> {message[CONFIGS.get("MESSAGE")]}'
#
#     # Отключение от сервера
#     elif message['action'] == 'quit':
#         pass
#
#     else:
#         client_logger.error(f'Получено некорректное сообщение: {message}')
#         raise ValueError


@log
def user_action(sock, user_name):
    """
    Обработчик поступающих команд от клиента
    :param sock: клиентский сокет
    :param user_name: имя текущего клиента
    :return:
    """
    while True:
        command = input('Введите "message" для приема и отправки сообщения, "exit" для выхода: ')
        if command == 'message':
            write_messages(sock, user_name)
        elif command == 'exit':
            send_message(sock, create_exit_message(user_name, CONFIGS), CONFIGS)
            client_logger.info('Завершение работы по команде пользователя')
            print('*** Завершение работы ***')
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана, попробуйте снова. \n'
                  'Введите "message" для приема и отправки сообщения, "exit" для выхода: ')


@log
def write_messages(sock, account_name):
    """
        Формирование и отправка на сервер сообщения клиента
        :param sock: клиентский сокет
        :param account_name: строка псевдонима
        :return message_dict: словарь сообщения клиента
    """
    receiver_name = input('Введите получателя сообщения -->  ')
    message_text = input('Введите сообщение --> ')

    message = {
        CONFIGS.get('ACTION'): 'msg',
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('SENDER'): account_name,
        CONFIGS.get('DESTINATION'): receiver_name,
        CONFIGS.get('MESSAGE'): message_text
    }

    client_logger.debug(f'Сформировано сообщение: {message}')

    client_logger.debug("Попытка отправки сообщения...")
    try:
        send_message(sock, message, CONFIGS)
        client_logger.info(f'Отправлено сообщение для пользователя {receiver_name}')
    except Exception:
        client_logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)


@log
def message_from_server(sock, user_name, CONFIGS):
    while True:
        try:
            message = get_message(sock, CONFIGS)
            if CONFIGS.get('RESPONSE') in message:
                if message[CONFIGS.get('RESPONSE')] == 200:
                    return '200 : OK'
                elif message[CONFIGS.get('RESPONSE')] == 400:
                    client_logger.debug(f'Получено сообщение от сервера: {message["response"]} {message["error"]}')
                    return f'400 : {message[CONFIGS.get("ERROR")]}'
            elif CONFIGS['ACTION'] in message and message[CONFIGS['ACTION']] == 'msg' and \
                    CONFIGS['SENDER'] in message and CONFIGS['DESTINATION'] in message \
                    and CONFIGS['MESSAGE'] in message and message[CONFIGS['DESTINATION']] == user_name:
                print(f'\nПолучено сообщение от пользователя {message[CONFIGS["SENDER"]]}: '
                      f'{message[CONFIGS["MESSAGE"]]}')
                client_logger.info(f'Получено сообщение от пользователя {message[CONFIGS["SENDER"]]}:'
                                   f' {message[CONFIGS["MESSAGE"]]}')
            # Отключение от сервера
            elif message['action'] == 'quit':
                break

            else:
                client_logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            client_logger.critical(f'Потеряно соединение с сервером.')
            break


@log
def create_client_socket(address, port, user_name):
    """
    создание соединения с сервером
    :param user_name: имя пользователя
    :param address: адрес сервера
    :param port: порт, по которому происходит подключение. по умолчанию 7777
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # Создать сокет TCP
        # Соединяется с сервером
        sock.connect((address, port))

        # Формируем сообщение о присутствии
        presence_message = create_presence_message(user_name, CONFIGS)

        # Отправляем сообщение о присутствии серверу
        send_message(sock, presence_message, CONFIGS)
        try:
            # response = get_message(sock, CONFIGS)
            hanlded_response = message_from_server(sock, user_name, CONFIGS)

            client_logger.info(f'Установлено соединение с сервером. Ответ сервера: {hanlded_response}')

        except (ValueError, json.JSONDecodeError):
            client_logger.error('Ошибка декодирования сообщения')
            sys.exit(1)

        except ConnectionRefusedError:
            client_logger.critical(f'Не удалось подключиться к серверу {address}:{port}, '
                                   f'запрос на подключение отклонён')
        else:
            # Запускает клиентский процесс приёма сообщений
            client_logger.debug('** Запуск потока \'thread-1\' для приёма сообщений **')
            receiver = threading.Thread(target=message_from_server, args=(sock, user_name, CONFIGS))
            receiver.daemon = True
            receiver.start()

            # Запускает отправку сообщений и взаимодействие с клиентом
            client_logger.debug('** Запуск потока \'thread-2\' для отправки сообщений **')
            client_logger.debug('** Процессы запущены **\n')
            user_interface = threading.Thread(target=user_action, args=(sock, user_name))
            user_interface.daemon = True
            user_interface.start()

            # Watchdog основной цикл, если один из потоков завершён,
            # то значит потеряно соединение или пользователь ввёл exit.
            # Поскольку все события обрабатываются в потоках,
            # достаточно завершить цикл.
            while True:

                time.sleep(1)
                if receiver.is_alive() and user_interface.is_alive():
                    continue
                break


@log
def client_main():
    client_logger.info('Клиент запущен!!')
    global CONFIGS
    CONFIGS = load_configs(is_server=False)
    args = parse(is_server=False)
    client_name = input('Введите имя пользователя: ')
    client_logger.info(f'Запущен клиент с парамертами: '
                       f'адрес сервера: {args.address}, порт: {args.port}, имя пользователя: {client_name}')
    create_client_socket(args.address, args.port, client_name)


if __name__ == "__main__":
    client_main()
