#!/usr/bin/env python3

import os
import unittest
import configparser

class RemoteControl:

    class Commands:
        @staticmethod
        def list():
            path_remote_control = os.path.join(os.path.dirname(__file__), 
                    '../.configs', f'remote_control.ini')

            config = configparser.ConfigParser()
            config.read(path_remote_control)
            
            return config

    class InvalidCommand(Exception):
        def __init__(self, message):
            self.message=message
            super().__init__(self.message)

    @staticmethod
    def __parser__(text):
        s_text = text.split(' ')
        if len(s_text) < 2:
            raise RemoteControl.InvalidCommand(text)

        return s_text[0], ' '.join(s_text[1:])

    @staticmethod
    def is_executable(text):
        try:
            cmd_type, cmd = RemoteControl.__parser__(text)
            if cmd_type == '$' and cmd in RemoteControl.Commands.list()['PROGRAMMED']:
                return True
        except RemoteControl.InvalidCommand as error:
            return False
        return False

    @staticmethod
    def is_whitelisted(number):
        return False

    @staticmethod
    def execute(text):
        raise RemoteControl.InvalidCommand(text)

class TestRemoteControl(unittest.TestCase):
    def test_parser(self):
        text = "$ reboot now"
        self.assertEqual(RemoteControl.__parser__(text), ('$', 'reboot now'))

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
        with self.assertRaises(RemoteControl.InvalidCommand, 
                RemoteControl.execute(invalid_text)) as excp:
            self.assertEqual(excp.message, invalid_text)

if __name__ == '__main__':
    unittest.main()
