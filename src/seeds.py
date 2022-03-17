#!/usr/bin/env python3

import base64
import json

from src.ledger import Ledger

class Seeds:

    def __init__(self, IMSI: str, seeder: bool=False):
        self.IMSI = IMSI
        self.seeder = seeder
        self.ledger = Ledger(IMSI=IMSI)

    def is_seed(self) -> bool:
        """Checks if current node can seed.
        In other to seed, an MSISDN and IMSI should be present in local db.
        """
        
        try:
            return self.ledger.find_seed()
        except Exception as error:
            raise error

    def is_seeder_message(self, data: base64) -> bool:
        """Checks if message is in format required for seeder update.
        """
        try:
            data = base64.b64decode(data)
        except Exception as error:
            raise error
        else:
            try:
                data = json.loads(data)
            except Exception as error:
                raise error
            else:
                if not "MSISDN" in data:
                    return False
                else:
                    # TODO check if valid MSISDN
                    return True

    def is_seed_message(self):
        return False

    def process_seed_message(self):
        return False

    def is_seeder(self) -> bool:
        """Checks if the current node can act as seeder.
        In other to be a seeder, seeder needs to be True in config and needs to be seed.
        """
        try:
            return self.seeder and self.is_seed()
        except Exception as error:
            raise error

    def ping(self):
        return False

    def make_seed(self, MSISDN: str):
        """Updates the ledger record for current IMSI with MSISDN.
        """

    def remote_seed(self):
        """Deletes the seed record for node.
        """
