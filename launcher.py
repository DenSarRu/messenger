"""
лаунчер проекта
"""
import os
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
processes = []
server_args = ['python3', 'server']
client_args = ['python3', 'client', '127.0.0.1']

while True:
    action = input('Выберите действие: q - выход , s - запустить сервер и клиенты, '
                   'x - закрыть все окна: ')

    if action == 's':
        number_of_clients = int(input('Укажите кол-во клиентов: '))
        processes.append(subprocess.Popen(server_args))
        time.sleep(2)
        for i in range(number_of_clients):
            processes.append(subprocess.Popen(client_args))
    elif action == 'x':
        while processes:
            process = processes.pop()
            process.kill()
    elif action == 'q':
        break
