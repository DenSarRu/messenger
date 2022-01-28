import ipaddress
import os
import socket
import subprocess
from tabulate import tabulate


def ip_address(host):
    try:
        if type(host) in (str, int):
            check = str(ipaddress.ip_address(host))
        else:
            return False
    except ValueError:
        try:
            check = socket.gethostbyname(host)
        except socket.gaierror:
            return False
    return check


def host_ping(list_of_hosts: list) -> list:
    """
    Функция проверки доступности сетевых узлов.
    Выполняет перебор ip-адресов и проверяет их доступность с выводом соответствующего сообщения
    («Узел доступен», «Узел недоступен»).
    :param list_of_hosts: список, в котором каждый сетевой узел должен быть представлен
    именем хоста или ip-адресом
    :return: список с результатом выполнения функции
    """
    result = []
    print('Выполняется проверка доступности сетевых узлов...')
    for host in list_of_hosts:
        verified_ip = ip_address(host)
        if verified_ip:
            with open(os.devnull, 'w') as DNULL:
                response = subprocess.call(
                    ["ping", "-c 4", verified_ip], stdout=DNULL
                )
            print(f'Host {verified_ip} is checked...')
            if response == 0:
                result.append(('reachable', str(host), f'[{verified_ip}]'))
                # print(f'Хост {host}\tip address: {verified_ip} доступен')
                continue
            else:
                result.append(('unreachable', str(host), f'[{verified_ip}]'))
                # print(f'Хост {host} ip address: {verified_ip} недоступен')
                continue
        result.append(('unreachable', str(host), '[ip адрес не определён]'))
        # print(f'Для хоста {host} не определён ip адрес')

    return result


def host_range_ping(check_network: str):
    """
    Функция перебора ip-адресов из заданного диапазона.
    По результатам проверки выводится соответствующее сообщение
    :param check_network: диапазон ip адресов вида XX.XX.XX.XX/XX
    :return: None
    """
    try:
        hosts = list(map(str, ipaddress.ip_network(network).hosts()))
    except ValueError as err:
        print(err)
    else:
        print(f'Запуск программы выполнения проверки доступности ip-адресов из заданного диапазона: {network}')
        return host_ping(hosts)


def host_range_ping_tab(test_network: str):
    dict_list = []
    result = host_range_ping(test_network)

    for host in result:
        dict_list.append(
            {
                host[0]: host[1]
            }
        )
    print(tabulate(dict_list, headers='keys', tablefmt="grid"))


if __name__ == "__main__":
    hosts_list = ['192.168.0.1', 'ya.ru', 'google.com', 'ya.hru', 'geekbrains.ru']
    print(f'\nЗапуск программы выполнения проверки доступности сетевых узлов: {hosts_list}')
    for response in host_ping(hosts_list):
        print(f'Host {response[1]} ip address {response[2]} is {response[0]}')

    print('\n')
    network = input('Введите адрес сети (например 80.0.1.0/28): ')
    for response in host_range_ping(network):
        print(f'Host {response[1]} ip address {response[2]} is {response[0]}')

    print('\n')
    host_range_ping_tab(network)
