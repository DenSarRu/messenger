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
import argparse
import socket
import time
import json


def parse():
    """
    Обработка параметров командной строки.
    client.py <addr> [<port>]:
            ○ addr — ip-адрес сервера, обязательный аргумент;
            ○ port — tcp-порт на сервере, по умолчанию 7777.
    :return: an object with two attributes: address, port
    """
    parser = argparse.ArgumentParser(description='Create socket and work with server')
    parser.add_argument("address",
                        help="server address for creating connection")
    parser.add_argument("-p", "--port", default=7777, type=int,
                        help="port for creating connection (default 7777)")

    return parser.parse_args()


def create_client_socket(address, port=7777):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))

    message_2_server = forming_message_to_server('presence')
    sock.send(bytes(message_2_server, encoding='utf-8'))

    message_from_server = sock.recv(640)
    check_server_message(message_from_server)

    sock.close()


def check_server_message(message):
    server_message = json.loads(message)
    print(f'Received message from server: {server_message}')


def forming_message_to_server(message_type: str):
    message = {
        "action": message_type,
        "time": time.time(),
        "type": "status",
        "user": {
            "account_name": "I_am_Your_CLIENT",
            "status": "Yep, I am here!"
        }
    }
    return json.dumps(message)


if __name__ == "__main__":
    args = parse()
    create_client_socket(args.address, args.port)
