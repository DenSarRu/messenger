import argparse


def parse(is_server=True):
    """
    Обработка параметров командной строки.
    для клиента:
        client.py 'address' ['port']:
                ○ addr — ip-адрес сервера, обязательный аргумент;
                ○ port — tcp-порт на сервере, по умолчанию 7777.
    для сервера:
        server.py [<addr>] [<port>]:
                ○ addr — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса);
                ○ port — TCP-порт для работы (по умолчанию использует 7777).
    :return: an object with two attributes: address, port
    """
    parser = argparse.ArgumentParser(description='Create socket and work with server')
    if is_server:
        parser.add_argument("-a", "--address", default='',
                            help="choose address for server (default ' ')")
    else:
        parser.add_argument("address",
                            help="server address for creating connection")
    parser.add_argument("-p", "--port", default=7777, type=int,
                        help="port for creating connection (default 7777)")

    return parser.parse_args()


# Для дальнейшей проработки
# def send_message(opened_socket, message, CONFIGS):
#     json_message = json.dumps(message)
#     response = json_message.encode(CONFIGS.get('ENCODING'))
#     opened_socket.send(response)
#
#
# def get_message(opened_socket, CONFIGS):
#     response = opened_socket.recv(CONFIGS.get('MAX_PACKAGE_LENGTH'))
#     if isinstance(response, bytes):
#         json_response = response.decode(CONFIGS.get('ENCODING'))
#         response_dict = json.loads(json_response)
#         if isinstance(response_dict, dict):
#             return response_dict
#         raise ValueError
#     raise ValueError


if __name__ == '__main__':
    parse()
