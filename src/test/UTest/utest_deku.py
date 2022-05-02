#!/usr/bin/env python3

import unittest

class Modem():
    imei='test_imei'
    model=None
    index=None
    state=None
    dbus_path=None
    power_state=None
    operator_code=None
    operator_name=None
    model=None
    manufacturer=None
    query_command=None

class UnitTestDeku(unittest.TestCase):
    def modem_send(self):
        pass

    def modem_available(self):
        pass

    def number_info(self):
        pass

    def change_modem_state(self):
        pass

    def modem_locked(self):
        pass

    def modem_ready(self):
        pass

    def modem_isp(self):
        pass
