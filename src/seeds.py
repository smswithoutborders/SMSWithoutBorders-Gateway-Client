#!/usr/bin/env python3

import base64
import json

from ledger import Ledger

class Seeds(Ledger):
    def __init__(self, IMSI: str):
        super().__init__(IMSI=IMSI)
        self.IMSI = IMSI

    def is_seed(self) -> bool:
        """Checks if current node can seed.
        In other to seed, an MSISDN and IMSI should be present in local db.
        """
        result = self.find_seed()
        if len(result) > 0:
            return True

        return False

    def is_seed_message(self):
        return False

    def process_seed_message(self):
        return False

    def update_state(self, state: str=None):
        """
        """

    def ping(self):
        return False

    def make_seed(self, MSISDN: str):
        """Updates the ledger record for current IMSI with MSISDN.
        """
        try:
            self.update_seed_MSISDN(seed_MSISDN=MSISDN)
        except Exception as error:
            raise error

    def remote_seed(self):
        """Deletes the seed record for node.
        """

