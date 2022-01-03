"""
 Файл сервисных функций проекта:
 utils.load_configs - загружает настройки проекта из файла
 utils.parse - обработка параметров командной строки
"""
import argparse
import json
import os
import sys
import yaml


def load_configs(is_server=True) -> dict:
    """
    загрузка параметров проекта в зависимости от вызывающего
    модуля - сервер или клиент
    :param is_server:
    :return: словарь с параметрами
    """
    config_keys = [
        'DEFAULT_PORT',
        'MAX_CONNECTIONS',
        'MAX_PACKAGE_LENGTH',
        'ENCODING',
        'ACTION',
        'TIME',
        'USER',
        'ACCOUNT_NAME',
        'PRESENCE',
        'RESPONSE',
        'ERROR'
    ]
    if not is_server:
        config_keys.append('DEFAULT_IP_ADDRESS')
    if not os.path.exists('config.yaml'):
        print('Файл конфигурации не найден')  # logging
        sys.exit(1)
    with open('config.yaml', encoding='utf-8') as config_file:
        CONFIGS = yaml.load(config_file, Loader=yaml.Loader)
    loaded_configs_keys = list(CONFIGS.keys())
    for key in config_keys:
        if key not in loaded_configs_keys:
            print(f'В файле конфигурации не хватает ключа: {key}')
            sys.exit(1)
    return CONFIGS


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


def send_message(opened_socket, message, CONFIGS):
    json_message = json.dumps(message)
    response = json_message.encode(CONFIGS.get('ENCODING'))
    opened_socket.send(response)


def get_message(opened_socket, CONFIGS):
    response = opened_socket.recv(CONFIGS.get('MAX_PACKAGE_LENGTH'))
    if not response:
        raise ValueError("we don't received any data")  # логирование (warning)
    if isinstance(response, bytes):
        json_response = response.decode(CONFIGS.get('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            return response_dict
        raise ValueError("incorrect data type received")  # логирование (warning)


if __name__ == '__main__':
    parse()
