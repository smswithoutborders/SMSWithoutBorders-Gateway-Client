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

    def process_seed_message(self, data: bytes) -> str:
        """Extracts the MSISDN from seeder message.
        """
        try:
            data = base64.b64decode(data)
        except Exception as error:
            raise error
        else:
            try:
                data = str(data, 'utf-8')
                data = json.loads(data)
            except Exception as error:
                raise error
            else:
                if not "MSISDN" in data:
                    raise Exception("Missing MSISDN")
                else:
                    return data["MSISDN"]

    def update_state(self, state: str=None):
        """
        """

    def update_seeder(self, seeder_MSISDN: str):
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

