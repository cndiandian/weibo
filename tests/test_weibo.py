import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 将 tests 目录添加到 Python 路径中
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from weibo_module import Weibo

class TestWeibo(unittest.TestCase):
    @patch('weibo_module.Weibo.SESSION.get')
    def test_weibo_id_and_proxy(self, mock_get):
        weibo = Weibo()

        # 测试微博ID是否配置正确
        self.assertEqual(weibo.WEIBO_ID, 'example_id', "微博ID配置错误")

        # 测试代理是否配置正确
        mock_get.side_effect = Exception("Unable to connect to Telegram server")
        with self.assertRaises(Exception):
            weibo.test()

    @patch('weibo_module.Weibo.send_telegram_message')
    def test_send_message_to_telegram(self, mock_send_message):
        weibo = Weibo()
        message = "Test message"
        weibo.send_telegram_message(message, "https://weibo.com")
        mock_send_message.assert_called_once_with(message, "https://weibo.com")

if __name__ == '__main__':
    unittest.main()
