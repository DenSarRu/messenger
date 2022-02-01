from decorators import log
from scripts.utils import parse
from server import Server



@log
def run():
    """
    Функция для запуска сервера
    :return:
    """
    args = parse()
    server = Server(args.address, args.port)
    server.run()


if __name__ == '__main__':
    run()
