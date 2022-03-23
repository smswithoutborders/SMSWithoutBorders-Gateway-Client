#!/usr/bin/env python3

import base64
import json
import time
import logging
import threading

from ledger import Ledger

class Seeds(Ledger):

    def __init__(self, IMSI: str, ping: bool=False):
        super().__init__(IMSI=IMSI)
        self.IMSI = IMSI
        self.ping = ping

        if ping:
            self.__ping__()

    def __ping_request__(self):
        try:
            MSISDN = self.get_MSISDN()
        except Exception as error:
            raise error
        else:
            while True:
                if MSISDN is not None:
                    logging.debug("Sending ping request for [%s]", MSISDN)
                else:
                    MSISDN = self.get_MSISDN()
                time.sleep(4)

    
    def __ping__(self):
        logging.debug("[*] Starting ping session")
        ping_thread = threading.Thread(target=self.__ping_request__, daemon=True)
        ping_thread.start()

    def is_seed(self) -> bool:
        """Checks if current node can seed.
        In other to seed, an MSISDN and IMSI should be present in local db.
        """
        result = self.find_seed()
        if len(result) > 0:
            return True

        return False


    def is_seed_message(data: bytes) -> bool:
        """
        """
        try:
            data = base64.b64decode(data)

        except Exception as error:
            return False

        else:
            try:
                data = str(data, 'utf-8')
                data = json.loads(data)

            except Exception as error:
                return False

            else:
                if "IMSI" in data:
                    return True

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

    def make_seed(self, MSISDN: str) -> int:
        """Updates the ledger record for current IMSI with MSISDN.
        """
        try:
            logging.debug("updating seed with MSISDN: %s", MSISDN)
            rowcount = self.update_seed_MSISDN(seed_MSISDN=MSISDN)
        except Exception as error:
            raise error
        else:
            return rowcount

    def remote_seed(self):
        """Deletes the seed record for node.
        """

    def get_MSISDN(self) -> str:
        """Fetches seeds MSISDN from ledger"""
        try:
            seed = self.find_seed()
        except Exception as error:
            raise error
        else:
            if len(seed) < 1:
                return None

            """
            seed[0][0] = IMSI
            seed[0][1] = MSISDN
            """
            return seed[0][1]
            
