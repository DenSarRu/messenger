import json
import os
import sys
import unittest
import time

from server import handle_message
from utils import load_configs


class ClientTestCase(unittest.TestCase):
    CONFIGS = load_configs()

    def setUp(self):
        self.correct_presence_message = {
            "action": 'presence',
            "time": time.time(),
            "user": {
                "account_name": "Guest",
            }
        }
        self.incorrect_presence_message = {
            'action': 'i am here',
            "time": time.time(),
            "user": {
                "account_name": "Guest",
            }
        }

    def test_correct_message(self):
        self.assertEqual(handle_message(self.correct_presence_message, self.CONFIGS), {'response': 200})

    def test_bad_message(self):
        self.assertEqual(handle_message(self.incorrect_presence_message, self.CONFIGS),
                         {'response': 400, 'error': 'Bad Request'})

    def test_message_max_length(self):
        """
        Проверка ограничения максимальной длины сообщения от клиента
        """
        pass


if __name__ == '__main__':
    unittest.main()
