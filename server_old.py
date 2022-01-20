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
def handle_message(message, CONFIGS) -> dict:
    """
    Функция для анализа сообщения, поступившего от клиента
    :param message: dict
    :return:
    """
    if CONFIGS.get('ACTION') in message \
            and message[CONFIGS.get('ACTION')] == CONFIGS.get('PRESENCE') \
            and CONFIGS.get('TIME') in message \
            and CONFIGS.get('USER') in message \
            and message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')] == 'Guest':
        server_logger.info('Correct request')
        return {CONFIGS.get('RESPONSE'): 200}
    elif message[CONFIGS.get('ACTION')] == 'msg':
        return message
    server_logger.warning('Incorrect request')
    return {
        CONFIGS.get('RESPONSE'): 400,
        CONFIGS.get('ERROR'): 'Bad Request'
    }


@log
def read_requests(r_clients, all_clients):
    messages = []
    for sock in r_clients:
        try:
            message = get_message(sock, CONFIGS)
            messages.append(message)
        except:
            server_logger.warning(f'Ошибка чтения сообщения. '
                                  f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
            print(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
            all_clients.remove(sock)
    return messages


@log
def write_responses(messages, w_clients, all_clients):
    for sock in w_clients:
        for message in messages:
            try:
                response = handle_message(message, CONFIGS)
                send_message(sock, response, CONFIGS)
            except:
                server_logger.warning(f'Ошибка отправки сообщения. '
                                      f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
                print(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')

                sock.close()
                all_clients.remove(sock)


@log
def create_server_socket(address='', port=7777):
    """
    Функция создает сокет и принимает сообщение клиента.
    :param address: IP-адрес для прослушивания (по умолчанию слушает все доступные адреса);
    :param port: TCP-порт для работы (по умолчанию используется 7777);
    :return:
    """
    clients = []

    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(CONFIGS.get('MAX_CONNECTIONS'))
    sock.settimeout(0.2)  # Таймаут для операций с сокетом
    server_logger.debug('Socket created')

    while True:
        try:
            client, client_address = sock.accept()
        except OSError as e:
            pass  # timeout вышел
        else:
            message_from_client = get_message(client,
                                              CONFIGS)  # получаем первое сообщение от только что подключивщегося клиента
            server_logger.info(f'accept request from client address: {client_address[0]} | port: {client_address[1]}')
            response = handle_message(message_from_client,
                                      CONFIGS)  # проверяем сообщение от только что подключивщегося клиента
            if response['response'] == 200:  # если запрос корректный, то заносим клиента в список
                clients.append(client)
            send_message(client, response, CONFIGS)  # отправляем ему ответ
        finally:
            # Проверить наличие событий ввода-вывода
            wait = 10
            r = []
            w = []
            try:
                r, w, e = select.select(clients, clients, [], wait)
            except:
                pass  # Ничего не делать, если какой-то клиент отключился

            requests = read_requests(r, clients)  # Сохраним запросы клиентов
            if requests:
                write_responses(requests, w, clients)  # Выполним отправку ответов клиентам
        #
        # try:
        #     message_from_client = get_message(client, CONFIGS)
        #     server_logger.debug(f'message: {str(message_from_client)}')
        #     response = handle_message(message_from_client, CONFIGS)
        #
        #     send_message(client, response, CONFIGS)
        #     client.close()
        # except(ValueError, json.JSONDecodeError) as e:
        #     server_logger.warning(f'Принято некорректное сообщение от клиента: {client_address}! {e}')
        #     client.close()


@log
def server_main():
    server_logger.info('Запуск эхо-сервера!')
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
