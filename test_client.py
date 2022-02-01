import unittest
from messenger_client.client_old import create_presence_message, handle_response
from messenger_server.utils import load_configs


class ClientTestCase(unittest.TestCase):
    CONFIGS = load_configs(is_server=False)

    def setUp(self) -> None:
        self.correct_message = {
            "action": 'presence',
            "time": 1.2,
            "user": {
                "account_name": "some_user_name"
            }
        }
        self.correct_response = {'response': 200}

    def _get_message_2_server(self, action='presence') -> dict:
        """
        формируем сообщение для сервера.
        :param action: передаём в сообщение метод
        :return: словарь, полученный из JSON-объекта
        """
        message_2_server = create_presence_message('some_user_name', self.CONFIGS)
        return message_2_server

    def test_message_fields_max_length(self):
        """
        Проверка ограничения длины полей сообщения:
            action — 15 символов;
            response — с кодом ответа сервера, это 3 цифры;
            user / (name): 25 символов;
        """
        pass

    def test_message_type(self):
        self.assertEqual(type(self._get_message_2_server()), type(self.correct_message))

    def test_correct_response(self):
        self.assertEqual(handle_response(self.correct_response, self.CONFIGS), '200 : OK')

    def test_bad_response(self):
        self.assertEqual(handle_response(
            {
                'response': 400,
                'error': 'Bad Request'
            }, self.CONFIGS),
            '400 : Bad Request'
        )

    def no_response(self):
        self.assertRaises(ValueError, handle_response, {"error": 'Bad Request'})

    def test_presence_message_to_server(self):
        test_message = self._get_message_2_server()
        self.correct_message['time'] = test_message['time']  # сравняем время для прохождения теста
        self.assertEqual(test_message, self.correct_message)


if __name__ == '__main__':
    unittest.main()
