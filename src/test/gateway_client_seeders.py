#!/usr/bin/env python3

import json
import logging
import base64
import unittest

from src.seeds import Seeds

logging.basicConfig(level='DEBUG')

class Test_Gateway_Client_Seeder(unittest.TestCase):
    IMSI = "TestIMSI"
    IMSISeeds = "TestIMSISeeds"
    IMSINoSeeds = "TestIMSINoSeed"
    
    """
    def test_insert_seed(self):
        raise Exception("Failed to insert seed")

    def test_message_seeder(self):
        raise Exception("Failed to message seeder")

    def test_process_seeder_message(self):
        raise Exception("Failed to process seeder message")
    """

    def test_is_seed(self):
        seed = Seeds(IMSI=Test_Gateway_Client_Seeder.IMSI)
        output = seed.is_seed()
        self.assertTrue(output)

    def test_is_seeder_message(self):
        seed = Seeds(IMSI=Test_Gateway_Client_Seeder.IMSI)
        """
        Comes through SMS (so base64 of a JSON dump)
        """
        sample_seeder_message = base64.b64encode(bytes(json.dumps(
            {"MSISDN":"TestMSISDN"}), 'utf-8'))
        output = seed.is_seeder_message(sample_seeder_message)
        self.assertTrue(output)

    def test_is_not_seeder_message(self):
        seed = Seeds(IMSI=Test_Gateway_Client_Seeder.IMSI)
        """
        Comes through SMS (so base64 of a JSON dump)
        """
        sample_seeder_message = base64.b64encode(bytes(json.dumps(
            {"NotMSISDN":"TestMSISDN"}), 'utf-8'))
        output = seed.is_seeder_message(sample_seeder_message)
        self.assertFalse(output)

    def test_is_seed_message(self):
        self.assertTrue(output)

    def test_process_seed_message(self):
        self.assertTrue(output)

    def test_can_seed_true(self):
        seed = Seeds(IMSI=Test_Gateway_Client_Seeder.IMSISeeds, seeder=True)
        output = seed.is_seeder()
        self.assertTrue(output)

    def test_can_seed_false(self):
        seed = Seeds(IMSI=Test_Gateway_Client_Seeder.IMSINoSeeds, seeder=False)
        output = seed.is_seeder()
        self.assertFalse(output)

    def test_ping(self):
        self.assertTrue(output)

    """
    def test_request_seed(self):
        return None

    def test_fetch_remote_seeds(self):
        return None

    def test_fetch_hardcoded_seeds(self):
        return None

    def test_make_seed(self):
        return False

    def test_remove_seed(self):
        return False
    """

if __name__ == '__main__':
    unittest.main()
