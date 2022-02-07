import sys
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from .db.database import ServerStorage
from .server import Server
from .server_gui import MainWindow, gui_create_model, HistoryWindow, \
    create_stat_model, ConfigWindow
from scripts.utils import load_configs

config = load_configs()
conflag_lock = threading.Lock()


class Console:
    """
    Класс обработчика для консольного режима
    """

    def __init__(self, address, port):
        self.server = Server(address, port, ServerStorage())

    def main(self):
        """
        Метод, запускающий консольный сервер
        :return:
        """
        self.server.run()


class Gui:
    """
    Класс обработчика для графического режима
    """

    def __init__(self, address, port):
        self.database = ServerStorage()
        self.server = Server(address, port, ServerStorage())
        self.server.handler = self
        self.server.daemon = True

        self.server_app = QApplication(sys.argv)

        self.main_window = MainWindow()
        self.main_window.statusBar().showMessage('Server Working')
        self.main_window.active_clients_table.setModel(
            gui_create_model(self.database))
        self.main_window.active_clients_table.resizeColumnsToContents()
        self.main_window.active_clients_table.resizeRowsToContents()
        self.main_window.refresh_button.triggered.connect(self.list_update)
        self.main_window.show_history_button.triggered.connect(
            self.show_statistics)
        self.main_window.config_btn.triggered.connect(self.server_config)

        self.stat_window = None
        self.rm_user_window = None
        self.config_window = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.list_update)

    def main(self):
        """
        Метод, запускающий графическую оболочку и необходимые компоненты
        :return:
        """
        self.server.start()
        self.timer.start(1000)
        self.server_app.exec_()

    def list_update(self):
        """
        Метод, обновляющий список подключённых клиентов
        :return:
        """
        if self.database.new_connection:
            self.main_window.active_clients_table.setModel(
                gui_create_model(self.database))
            self.main_window.active_clients_table.resizeColumnsToContents()
            self.main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                self.database.new_connection = False

    def show_statistics(self):
        """
        Метод создающий окно со статистикой клиентов.
        :return:
        """
        self.stat_window = HistoryWindow()
        self.stat_window.history_table.setModel(
            create_stat_model(self.database))
        self.stat_window.history_table.resizeColumnsToContents()
        self.stat_window.history_table.resizeRowsToContents()
        self.stat_window.show()

    def server_config(self):
        """
        Метод создающий окно с настройками сервера.
        :return:
        """
        self.config_window = ConfigWindow()
        self.config_window.save_btn.clicked.connect(self.save_server_config)

    def save_server_config(self):
        """
        Метод проверки и сохранения настроек сервера.
        :return:
        """
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = self.config_window.db_path.text()
        config['SETTINGS']['Database_file'] = self.config_window.db_file.text()
        try:
            port = int(self.config_window.port.text())
        except ValueError:
            message.warning(self.config_window, 'Ошибка',
                            'Порт должен быть числом')
        else:
            config['SETTINGS']['listen_address'] = self.config_window.ip.text()
