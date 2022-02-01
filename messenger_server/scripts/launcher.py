import subprocess
import time

processes = []
server_args = ['python3',  'messenger_server.py']
client_args = ['python3',  'messenger_client.py', '127.0.0.1']

while True:
    action = input('Выберите действие: q - выход , s - запустить сервер и клиенты, x - закрыть все окна: ')

    if action == 'q':
        break
    elif action == 's':
        processes.append(subprocess.run(server_args))
        time.sleep(2)
        processes.append(subprocess.Popen(client_args))
        processes.append(subprocess.Popen(client_args))
    elif action == 'x':
        while processes:
            process = processes.pop()
            process.kill()
