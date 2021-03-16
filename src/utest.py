#!/bin/python

import unittest as utest
from libs.lmodem import Modem

class libModemTest(utest.TestCase):
    def test_info(self):
        with open("utest_files/mmcli_sim/sim_modem.txt") as fileSimModem:
            simModem = fileSimModem.read()

            modem = Modem('0')
            simModemInfo = modem.extractInfo( simModem )

            self.assertEqual( simModemInfo['modem.3gpp.imei'], '358812037638331' )

            # TODO: Make this kind of serialization into an object possible
            self.assertEqual( simModemInfo['modem']['3gpp']['imei'], '358812037638331' )

    '''
    def test_send_sms(self):

    def test_read_sms(self):

    def test_ussd(self):
    '''


if __name__ == '__main__':
    utest.main()
