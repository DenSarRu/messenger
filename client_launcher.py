import logging
import os
import select
import socket
import threading

from log import client_log_config
from client.client import Client
from scripts.decorators import log
from scripts.utils import parse, get_message, send_message, load_configs

# from client.db.database import Client

dir_path = os.path.dirname(os.path.realpath(__file__))
client_logger = logging.getLogger('client_log')
CONFIGS = {}


@log
def main():
    """Основная функция"""
    CONFIGS = load_configs()
    args = parse(is_server=False)
    client = Client(args.address, args.port)
    client.run()


if __name__ == '__main__':
    main()
