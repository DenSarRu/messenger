from decorators import log
from scripts.utils import parse
from client import Client


@log
def run():
    """
    Функция для запуска сервера
    :return:
    """
    args = parse(is_server=False)
    server = Client(args.address, args.port)
    server.run()


if __name__ == '__main__':
    run()
