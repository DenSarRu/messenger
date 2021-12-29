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
import socket
import time
import json

from utils import parse


def create_client_socket(address, port=7777):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))

    presence_message_2_server = forming_message_to_server('presence')
    sock.send(bytes(presence_message_2_server, encoding='utf-8'))

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
    args = parse(is_server=False)
    create_client_socket(args.address, args.port)
