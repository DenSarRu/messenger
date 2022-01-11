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
import socket
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
    server_logger.warning('Incorrect request')
    return {
        CONFIGS.get('RESPONSE'): 400,
        CONFIGS.get('ERROR'): 'Bad Request'
    }


@log
def create_server_socket(address='', port=7777):
    """
    Функция создает сокет и принимает сообщение клиента.
    :param address: IP-адрес для прослушивания (по умолчанию слушает все доступные адреса);
    :param port: TCP-порт для работы (по умолчанию использует 7777);
    :return:
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(CONFIGS.get('MAX_CONNECTIONS'))
    server_logger.debug('Socket created')

    while True:
        client, client_address = sock.accept()
        server_logger.info(f'accept request from client address: {client_address[0]} | port: {client_address[1]}')

        try:
            message_from_client = get_message(client, CONFIGS)
            server_logger.debug(f'message: {str(message_from_client)}')
            response = handle_message(message_from_client, CONFIGS)

            send_message(client, response, CONFIGS)
            client.close()
        except(ValueError, json.JSONDecodeError) as e:
            server_logger.warning(f'Принято некорректное сообщение от клиента: {client_address}! {e}')
            client.close()


@log
def server_main():
    server_logger.info('Запуск сервера!')
    global CONFIGS
    CONFIGS = load_configs()
    args = parse()
    create_server_socket(args.address, args.port)


if __name__ == "__main__":
    server_main()
