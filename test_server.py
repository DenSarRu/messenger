import json
import unittest
import time

from server import check_client_message, forming_response_to_client


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.test_message = {
            "action": 'presence',
            "time": time.time(),
            "user": {
                "account_name": "some_user_name",
                "status": "Yep, I am here!"
            }
        }

    def test_check_message_function(self):
        message = json.dumps(self.test_message)

        self.assertEqual(check_client_message(message, ' '),
                         ('presence', {'account_name': 'some_user_name', 'status': 'Yep, I am here!'})
                         )

    def test_forming_response_to_client(self):
        message_from_client = ('presence', {'account_name': 'some_user_name', 'status': 'Yep, I am here!'})
        response_2_client = json.loads(forming_response_to_client(message_from_client))

        self.assertEqual(response_2_client['response'], '100')

    def test_message_max_length(self):
        """
        Проверка ограничения максимальной длины сообщения от клиента
        """
        pass


if __name__ == "__main__":
    unittest.main()
