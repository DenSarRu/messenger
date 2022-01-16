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
from decorators import log
from utils import parse, load_configs, send_message, get_message

client_logger = logging.getLogger('client_log')
CONFIGS = dict()


@log
def create_presence_message(account_name, CONFIGS):
    if not isinstance(account_name, str):
        client_logger.warning(f"Ошибка указания имени пользователя {account_name}")
        raise TypeError
    if len(account_name) > 25:
        client_logger.warning("create_message: Username Too Long Error")
        raise ValueError
    message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): account_name
        }
    }
    return message


@log
def create_authenticate_message(account_name: str, account_password: str) -> dict:
    message = {
        CONFIGS.get('ACTION'): CONFIGS.get('AUTHENTICATE'),
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): account_name,
            CONFIGS.get('PASSWORD'): account_password
        }
    }
    return message


@log
def handle_response(message, CONFIGS):
    if CONFIGS.get('RESPONSE') in message:
        if message[CONFIGS.get('RESPONSE')] == 200:
            return '200 : OK'
        return f'400 : {message[CONFIGS.get("ERROR")]}'
    elif message['action'] == 'msg':
        return f'получено сообщение: {message[CONFIGS.get("MESSAGE")]}'
    raise ValueError


def user_action():
    msg = input('Введите "s" для отправки сообщения, "r" для получения сообщений, "exit" для выхода: ')
    return msg


def write_messages(sock):
    message_text = input('your message --> ')
    message = {
        CONFIGS.get('ACTION'): 'msg',
        CONFIGS.get('TIME'): time.time(),
        CONFIGS.get('MESSAGE'): message_text
    }
    client_logger.debug("Sending message...")
    send_message(sock, message, CONFIGS)


def read_messages(sock):
    while True:
        message = get_message(sock, CONFIGS)
        print(handle_response(message, CONFIGS))
        # print(message)


@log
def create_client_socket(address, port=7777):
    """
    создание соединения с сервером
    :param address: адрес сервера
    :param port: порт, по которому происходит подключение. по умолчанию 7777
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # Создать сокет TCP
        sock.connect((address, port))

        client_logger.debug('Установлено соединение с сервером')
        presence_message = create_presence_message('Guest', CONFIGS)
        send_message(sock, presence_message, CONFIGS)
        try:
            response = get_message(sock, CONFIGS)
            hanlded_response = handle_response(response, CONFIGS)
            client_logger.info(f'Ответ от сервера: {hanlded_response}')
            if response['response'] == 200:
                while True:
                    mode = user_action()
                    if mode == 's':
                        write_messages(sock)
                    elif mode == 'r':
                        read_messages(sock)
                    elif mode == 'exit':
                        break
            else:
                client_logger.warning('Получен невнятный ответ от сервера!')

        except (ValueError, json.JSONDecodeError):
            client_logger.warning('Ошибка декодирования сообщения')


@log
def client_main():
    client_logger.info('Клиент запущен!!')
    global CONFIGS
    CONFIGS = load_configs(is_server=False)
    args = parse(is_server=False)
    create_client_socket(args.address, args.port)


if __name__ == "__main__":
    client_main()
