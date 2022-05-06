#!/usr/bin/env python3

import base64
import json
import time
import logging
import requests
import threading

from ledger import Ledger
from seeders import Seeders

class Seeds(threading.Event, Ledger):

    class InvalidSeedState(Exception):
        def __init__(self):
            self.message = "Invalid seed state"
            super().__init__(self.message)


    def __init__(self, 
            IMSI: str, 
            seeder_timeout: float=300.0) -> None:

        Ledger.__init__(self, IMSI=IMSI)
        super().__init__()

        self.IMSI = IMSI
        self.__seeder_timeout = seeder_timeout
        self.kill_seed_ping = False

    def remote_search(self, remote_gateway_servers) -> str:
        """Checks with the remote Gateway servers for MSISDN.
        """
        logging.info("[*] Searching for current seed on remote servers...")

        for gateway_server in remote_gateway_servers:
            gateway_server = gateway_server % (self.IMSI)
            logging.debug("-> searching server: %s", gateway_server )

            try:
                results = requests.get(gateway_server, json={})
                logging.debug(results.text)

            except Exception as error:
                # logging.exception(error)
                logging.error(error)

            else:
                if not results.text == '':
                    return results.text

        return ''

    def ping_keepalive(self, ping_servers: list, 
            ping_duration: float) -> None:

        while True and not self.kill_seed_ping:
            try:
                MSISDN = self.get_MSISDN()
            except Exception as error:
                logging.error(error)
            else:
                if MSISDN is not None:
                    seeder = Seeders(MSISDN=MSISDN)
                    logging.debug("Sending ping request for [%s]", MSISDN)

                    ping_data = { 
                            "IMSI":self.IMSI,
                            "MSISDN":MSISDN,
                            "seed_type":"seeder" if seeder.is_seeder() else "seed"}
                    logging.debug("Ping data: %s", ping_data)

                    for ping_server in ping_servers:
                        try:
                            logging.debug("pinging: %s", ping_server)
                            results = requests.post(ping_server, json=ping_data)

                            logging.debug("Ping results: [%s] %s", MSISDN, results.text)
                        except Exception as error:
                            logging.error(error)

                    # TODO: Configuration goes here to determine ping time
            time.sleep(ping_duration)


    def stop_ping(self) -> None:
        """
        """
        logging.debug("[*] Stopping ping session")

        self.kill_seed_ping = True
    
    def start_pinging(self, ping_servers: list = [], ping_duration: float = 30.0):
        """Initializing ping request to requested server.
        """
        logging.debug("[*] Starting ping session")

        try:
            ping_thread = threading.Thread(
                    target=self.ping_keepalive, 
                    args=(ping_servers, ping_duration,),
                    daemon=True)
            ping_thread.start()

        except Exception as error:
            raise error

    def is_seed(self) -> bool:
        """Checks if current node can seed.
        In other to seed, an MSISDN and IMSI should be present in local db.
        """
        try:
            result = self.find_seed()
        except Exception as error:
            logging.exception(error)
        else:
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

    def update_state(self, seeder_MSISDN: str, state: str='requested'):
        """
        """
        try:
            states = ['requested', 'confirmed']
            logging.debug("updating seed with state: %s", state)

            if state in states:
                rowcount = self.update_seed_state(seeder_MSISDN=seeder_MSISDN, state=state)

            else:
                raise Seeds.InvalidSeedState()

        except Exception as error:
            raise error
        else:
            return rowcount


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
            seed[0][2] = SEEDER_MSISDN
            seed[0][3] = state
            seed[0][4] = date (datetime)
            """
            return seed[0][1]
            
    def can_request_MSISDN(self) -> bool:
        """Checks if seed can request for MSISDN from seeder

        Returns:
            bool
        """
        try:
            seed = self.find_seed_record()
            logging.debug("%s", seed)

        except Exception as error:
            raise error

        else:
            if len(seed) < 1:
                return True

            if seed[0][3] == "requested":

                """checks if timeout has reached"""
                state_time = float(seed[0][4])
                now_time = time.time()
                
                if now_time <= (state_time + self.__seeder_timeout):
                    """ """
                    logging.debug("Request has not expired: %d seconds remaining", 
                            (state_time + self.__seeder_timeout) - now_time)

                    return False

        return True
