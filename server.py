""""
Функции сервера:
    ● принимает сообщение клиента;
    ● формирует ответ клиенту;
    ● отправляет ответ клиенту;
    ● имеет параметры командной строки:
        ○ -p <port> — TCP-порт для работы (по умолчанию использует 7777);
        ○ -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import socket
import json
import time
from utils import parse


def create_server_socket(address='', port=7777):
    """
    Функция создает сокет и принимает сообщение клиента.
    :param address: IP-адрес для прослушивания (по умолчанию слушает все доступные адреса);
    :param port: TCP-порт для работы (по умолчанию использует 7777);
    :return:
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(5)

    while True:
        client, addr = sock.accept()
        print(f'accept request from client {addr}')

        data = client.recv(640)
        if not data:
            print(f"we don't received any data from {addr}")

        message_from_client = check_client_message(data, addr)
        # print(message_from_client)
        message_to_client = forming_response_to_client(message_from_client)

        client.send(bytes(message_to_client, encoding='utf-8'))
        client.close()


def check_client_message(message: json, address: str) -> tuple:
    """
    Функция для анализа сообщения, поступившего от клиента
    :param message: JSON object
    :param address: адрес клиента
    :return:
    """
    client_message = json.loads(message)

    print(f'"action" message from client {address}: {client_message["action"]}')
    return client_message['action'], client_message['user']


def forming_response_to_client(message_from_client):
    response = ''

    if message_from_client[0] == 'presence':
        response = '100'

    message = {
        "response": response,
        "time": time.time(),
    }
    return json.dumps(message)


if __name__ == "__main__":

    args = parse()
    create_server_socket(args.address, args.port)
