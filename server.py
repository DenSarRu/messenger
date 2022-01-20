""""
Функции сервера:
    ● принимает сообщение клиента;
    ● формирует ответ клиенту;
    ● отправляет ответ клиенту;
    ● имеет параметры командной строки:
        ○ -p <port> — TCP-порт для работы (по умолчанию использует 7777);
        ○ -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import json
import logging
import select
from socket import socket, AF_INET, SOCK_STREAM

from log import server_log_config
from decorators import log

from utils import parse, get_message, send_message, load_configs

server_logger = logging.getLogger('server_log')
CONFIGS = dict()


@log
def parse_client_msg(message, messages_list, sock, clients_list, names):
    """
        Обработчик сообщений клиентов
        :param message: словарь сообщения
        :param messages_list: список сообщений
        :param sock: клиентский сокет
        :param clients_list: список клиентских сокетов
        :param names: список зарегистрированных клиентов
        :return: словарь ответа
        """
    server_logger.debug(f'Разбор сообщения от клиента: {message}')

    # возвращает сообщение о присутствии
    if CONFIGS.get('ACTION') in message \
            and message[CONFIGS.get('ACTION')] == CONFIGS.get('PRESENCE') \
            and CONFIGS.get('TIME') in message:

        # авторизация
        if message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')] not in names.keys():
            names[message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]] = sock
            send_message(sock, {CONFIGS.get('RESPONSE'): 200}, CONFIGS)
            server_logger.info(f'Авторизован клиент: {message[CONFIGS.get("USER")][CONFIGS.get("ACCOUNT_NAME")]}')
        else:
            response = {
                CONFIGS.get('RESPONSE'): 400,
                CONFIGS.get('ERROR'): 'Имя пользователя уже занято.'
            }
            server_logger.warning(
                f'Повторная попытка авторизации клиента: {message[CONFIGS.get("USER")][CONFIGS.get("ACCOUNT_NAME")]}!'
                f'Отказ. Имя пользователя уже занято.')
            send_message(sock, response, CONFIGS)
            clients_list.remove(sock)
            sock.close()
        return

    # формирует очередь сообщений
    elif CONFIGS.get('ACTION') in message and message[CONFIGS.get('ACTION')] == 'msg' and \
            CONFIGS.get('SENDER') in message and CONFIGS.get('DESTINATION') in message and \
            CONFIGS.get('MESSAGE') in message and CONFIGS.get('TIME') in message:
        server_logger.debug(f'формирует очередь сообщений')
        messages_list.append(message)
        return

    # выход клиента
    elif CONFIGS.get('ACTION') in message and message[CONFIGS.get('ACTION')] == 'exit' and \
            CONFIGS.get('ACCOUNT_NAME') in message[CONFIGS.get('USER')]:
        server_logger.debug(f'выход клиента {message[CONFIGS.get("USER")][CONFIGS.get("ACCOUNT_NAME")]}')
        response = {
            "action": "quit"
        }
        send_message(sock, response, CONFIGS)

        clients_list.remove(names[message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]])
        names[message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]].close()
        del names[message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]]
        return

    # возвращает сообщение об ошибке
    else:
        response = {
            CONFIGS.get('RESPONSE'): 400,
            CONFIGS.get('ERROR'): 'Bad Request',
        }
        send_message(sock, response, CONFIGS)
        return


@log
def route_client_msg(message, names, clients):
    """
    Адресная отправка сообщений.
    :param message: словарь сообщения
    :param names: список зарегистрированных клиентов
    :param clients: список слушающих клиентских сокетов
    :return:
    """
    if message[CONFIGS.get('DESTINATION')] in names and names[message[CONFIGS.get('DESTINATION')]] in clients:
        send_message(names[message[CONFIGS.get('DESTINATION')]], message, CONFIGS)
        server_logger.info(f'Отправлено сообщение пользователю {message[CONFIGS.get("DESTINATION")]} '
                           f'от пользователя {message[CONFIGS.get("SENDER")]}.')
    elif message[CONFIGS.get('DESTINATION')] in names and names[message[CONFIGS.get('DESTINATION')]] not in clients:
        raise ConnectionError
    else:
        server_logger.error(
            f'Пользователь {message[CONFIGS.get("DESTINATION")]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')


@log
def create_server_socket(address='', port=7777):
    """
    Функция создает сокет и принимает сообщение клиента.
    :param address: IP-адрес для прослушивания (по умолчанию слушает все доступные адреса);
    :param port: TCP-порт для работы (по умолчанию используется 7777);
    :return:
    """
    # Создает TCP-сокет сервера
    server_tcp = socket(AF_INET, SOCK_STREAM)

    # Связывает сокет с ip-адресом и портом сервера
    server_tcp.bind((address, port))

    # Таймаут для операций с сокетом
    server_tcp.settimeout(0.5)

    # Запускает режим прослушивания
    server_tcp.listen(CONFIGS.get('MAX_CONNECTIONS'))

    server_tcp.settimeout(0.2)  # Таймаут для операций с сокетом
    server_logger.debug('Socket created')

    # Список клиентов и очередь сообщений
    all_clients = []
    all_messages = []

    # Словарь зарегистрированных клиентов: ключ - имя пользователя, значение - сокет
    all_names = dict()

    while True:
        # Принимает запрос на соединение
        # Возвращает кортеж (новый TCP-сокет клиента, адрес клиента)
        try:
            client_tcp, client_address = server_tcp.accept()
        except OSError:
            pass
        else:
            server_logger.info(f'Установлено соедение с клиентом {client_address}')
            all_clients.append(client_tcp)

        r_clients = []
        w_clients = []
        errs = []

        # Запрашивает информацию о готовности к вводу, выводу и о наличии исключений для группы дескрипторов сокетов
        try:
            if all_clients:
                r_clients, w_clients, errs = select.select(all_clients, all_clients, [], 0)
        except OSError:
            pass

        # Чтение запросов из списка клиентов
        if r_clients:
            for r_sock in r_clients:
                try:
                    parse_client_msg(get_message(r_sock, CONFIGS), all_messages, r_sock, all_clients, all_names)
                except Exception as ex:
                    server_logger.error(f'Клиент отключился от сервера. '
                                        f'Тип исключения: {type(ex).__name__}, аргументы: {ex.args}')
                    all_clients.remove(r_sock)

        # Роутинг сообщений адресатам
        for msg in all_messages:
            try:
                route_client_msg(msg, all_names, w_clients)
            except Exception:
                server_logger.info(f'Связь с клиентом {msg[CONFIGS.get("DESTINATION")]} была потеряна')
                all_clients.remove(all_names[msg[CONFIGS.get("DESTINATION")]])
                del all_names[msg[CONFIGS.get("DESTINATION")]]
        all_messages.clear()


@log
def server_main():
    server_logger.info('Запуск сервера!')
    global CONFIGS
    CONFIGS = load_configs()
    args = parse()
    create_server_socket(args.address, args.port)


if __name__ == "__main__":
    try:
        server_main()
    except Exception as e:
        server_logger.error('Exception: {}'.format(str(e)))
    server_logger.info("Server stopped")
