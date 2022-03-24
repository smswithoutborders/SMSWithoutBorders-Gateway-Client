#!/usr/bin/env python3

import base64
import json
import time
import logging
import requests
import threading

from ledger import Ledger
from seeders import Seeders

class Seeds(Ledger):

    def __init__(self, 
            IMSI: str, 
            ping: bool=False, 
            ping_servers: list=[]) -> None:

        super().__init__(IMSI=IMSI)
        self.IMSI = IMSI
        self.ping = ping
        self.ping_servers = ping_servers

        if ping:
            self.__ping__()

    def __ping_request__(self) -> None:
        try:
            while True:
                MSISDN = self.get_MSISDN()
                if MSISDN is not None:
                    seeder = Seeders(MSISDN=MSISDN)
                    logging.debug("Sending ping request for [%s]", MSISDN)

                    ping_data = { 
                            "IMSI":self.IMSI,
                            "MSISDN":MSISDN,
                            "seeder":seeder.is_seeder()}
                    logging.debug("Ping data: %s", ping_data)

                    for ping_server in self.ping_servers:
                        results = requests.post(ping_server, json=ping_data)

                        logging.debug("Ping results: %s", results.text)

                    # TODO: Configuration goes here to determine ping time
                time.sleep(4)
        except Exception as error:
            raise error

    
    def __ping__(self) -> None:
        logging.debug("[*] Starting ping session")
        self.ping_thread = threading.Thread(target=self.__ping_request__, daemon=True)
        self.ping_thread.start()

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
            
