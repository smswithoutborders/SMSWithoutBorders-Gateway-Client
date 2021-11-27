#!/usr/bin/env python3

import os
import unittest
import subprocess
import configparser

class RemoteControl:

    class Whitelist:
        @staticmethod
        def list():
            path_remote_control = os.path.join(os.path.dirname(__file__), 
                    '../.configs/remote_control', 
                    f'example.remote_control_auth.ini')

            config = configparser.ConfigParser()
            config.read(path_remote_control)
            
            return config['WHITELIST']

    class Commands:
        @staticmethod
        def list(cmd_type):
            path_remote_control = os.path.join(os.path.dirname(__file__), 
                    '../.configs/remote_control', f'remote_control.ini')

            config = configparser.ConfigParser()
            config.read(path_remote_control)
            
            if cmd_type == '$':
                return config['COMMANDS']
            return []

    class InvalidCommand(Exception):
        def __init__(self, cmd, cmd_type=None):
            self.cmd=cmd
            self.cmd_type=None
            super().__init__(self.cmd)

    class MissingExecutionValue(Exception):
        def __init__(self, message):
            self.message=message
            super().__init__(self.message)

    class SubProcessError(subprocess.CalledProcessError):
        def __init__(self, cmd, output=None, returncode=None):
            self.cmd=cmd
            self.output=output
            self.returncode=returncode
            super().__init__(cmd=self.cmd, returncode=returncode)

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
            if cmd in RemoteControl.Commands.list(cmd_type):
                return True
        except RemoteControl.InvalidCommand as error:
            return False
        except Exception as error:
            raise error
        return False

    @staticmethod
    def is_whitelist(number):
        return number in RemoteControl.Whitelist.list()

    @staticmethod
    def __exec__(cmd_type, cmd):
        if cmd_type == '$':
            s_cmd = cmd.split(' ')
            try: 
                cmd_output = subprocess.check_output(s_cmd, 
                        stderr=subprocess.STDOUT).decode('unicode_escape')

                return cmd_output

            except subprocess.CalledProcessError as error:
                raise RemoteControl.SubProcessError(error)
            except FileNotFoundError as error:
                raise RemoteControl.SubProcessError(cmd=cmd, 
                        output=error.strerror, returncode=error.errno)
        else:
            raise RemoteControl.InvalidCommand(cmd, cmd_type)


    @staticmethod
    def execute(text):
        cmd_type, cmd = RemoteControl.__parser__(text)
        commands = RemoteControl.Commands.list(cmd_type)
        if cmd in commands:
            if commands[cmd] != '':
                try:
                    RemoteControl.__exec__( cmd_type=cmd_type, cmd=commands[cmd] )
                except RemoteControl.SubProcessError as error:
                    raise error
                return True
            else:
                raise RemoteControl.MissingExecutionValue(text)
        else:
            raise RemoteControl.InvalidCommand(text)

class TestRemoteControl(unittest.TestCase):
    def test_parser(self):
        text = "$ test_reboot now"
        self.assertEqual(RemoteControl.__parser__(text), ('$', 'test_reboot now'))

    def test_is_executable(self):
        text = "$ test_reboot"
        self.assertTrue(RemoteControl.is_executable(text))

    def test_is_whitelist(self):
        number = "+000000000"
        self.assertTrue(RemoteControl.is_whitelist(number))

    def test_execute(self):
        text = "$ reboot"
        self.assertTrue(RemoteControl.execute(text))

    def test_execute_raises_exception_invalid_command(self):
        invalid_text = "$test_reboot"
        with self.assertRaises(RemoteControl.InvalidCommand) as excp:
            RemoteControl.execute(invalid_text)

    def test_execute_raises_missing_execution(self):
        text = "$ test_reboot"
        with self.assertRaises(RemoteControl.MissingExecutionValue) as excp:
            RemoteControl.execute(text)

    def test_execute_raises_subprocess_error(self):
        text = "$ test_reboot_value"
        with self.assertRaises(RemoteControl.SubProcessError) as excp:
            RemoteControl.execute(text)

if __name__ == '__main__':
    unittest.main()
