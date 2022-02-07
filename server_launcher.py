import logging
import os

from log import server_log_config
from scripts.decorators import log
from scripts.utils import parse
from server.handler import Console, Gui


dir_path = os.path.dirname(os.path.realpath(__file__))
server_logger = logging.getLogger('server_log')
CONFIGS = {}


@log
def main():
    """Основная функция"""

    args = parse()
    if args.m == 'console':
        handler = Console(args.address, args.port)
    else:
        handler = Gui(args.address, args.port)
    handler.main()


if __name__ == '__main__':
    main()
