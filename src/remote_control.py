#!/usr/bin/env python3

import unittest

class RemoteControl:

    class InvalidCommand(Exception):
        def __init__(self, message):
            self.message=message
            super().__init__(self.message)

    @staticmethod
    def is_executable(text):
        return False

    @staticmethod
    def is_whitelisted(number):
        return False

    @staticmethod
    def execute(text):
        raise RemoteControl.InvalidCommand(text)

class TestRemoteControl(unittest.TestCase):
    def test_is_executable(self):
        text = "$ reboot"
        self.assertTrue(RemoteControl.is_executable(text))

    def test_is_whitelisted(self):
        number = "+237000000000"
        self.assertTrue(RemoteControl.is_whitelisted(number))

    def test_execute(self):
        text = "$ reboot"
        self.assertTrue(RemoteControl.execute(text))

    def test_execute_raises_exception(self):
        invalid_text = "$reboot"
        with self.assertRaises(RemoteControl.InvalidCommand, RemoteControl.execute(invalid_text)) as excp:
            self.assertEqual(excp.message, invalid_text)


if __name__ == '__main__':
    unittest.main()
