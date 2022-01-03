"""
    Функции клиента:
        ● сформировать presence-сообщение;
        ● отправить сообщение серверу;
        ● получить ответ сервера;
        ● разобрать сообщение сервера;
        ● параметры командной строки скрипта client.py <addr> [<port>]:
            ○ addr — ip-адрес сервера;
            ○ port — tcp-порт на сервере, по умолчанию 7777.
"""
import json
import logging
import socket
import time
from log import client_log_config

from utils import parse, load_configs, send_message, get_message

client_logger = logging.getLogger('client_log')
CONFIGS = dict()


def create_presence_message(account_name):
    message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): account_name
        }
    }
    return message


def handle_response(message):
    if CONFIGS.get('RESPONSE') in message:
        if message[CONFIGS.get('RESPONSE')] == 200:
            return '200 : OK'
        return f'400 : {message[CONFIGS.get("ERROR")]}'
    raise ValueError


def create_client_socket(address, port=7777):
    """
    создание соединения с сервером
    :param address: адрес сервера
    :param port: порт, по которому происходит подключение. по умолчанию 7777
    :return:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))
    client_logger.debug('Установлено соединение с сервером')
    presence_message = create_presence_message('Guest')
    send_message(sock, presence_message, CONFIGS)
    try:
        response = get_message(sock, CONFIGS)
        hanlded_response = handle_response(response)
        client_logger.info(f'Ответ от сервера: {response}')
        print(hanlded_response)
    except (ValueError, json.JSONDecodeError):
        client_logger.warning('Ошибка декодирования сообщения')

    sock.close()


def client_main():
    client_logger.info('Клиент запущен!!')
    global CONFIGS
    CONFIGS = load_configs()
    args = parse(is_server=False)
    create_client_socket(args.address, args.port)


if __name__ == "__main__":
    client_main()
