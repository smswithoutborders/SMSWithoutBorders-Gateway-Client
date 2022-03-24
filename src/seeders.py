#!/usr/bin/env python3

import os
import logging
import json
import base64
import subprocess

from ledger import Ledger

class Seeders(Ledger):
    def __init__(self, 
            MSISDN: str, 
            _id: str = None, 
            seeder: bool = False) -> None:


        super().__init__(MSISDN=MSISDN)
        self._id = _id
        self.seeder = seeder
        self.MSISDN = MSISDN

    @staticmethod
    def _filter(seeders: list, filters: dict) -> list:
        """
        """
        seeders = []
        return seeders

    @staticmethod
    def request_remote_seeders() -> list:
        """Checks with the remote Gateway servers for remote seeders.
        """
        try:
            for gateway_server in self.gateway_servers:
                logging.debug("Requesting remote seeders from: %s", gateway_server)
                try:
                    results = requests.post(gateway_server, json={})

                    if not results.status_code == 200:
                        results.raise_for_status()

                    results_json = results.json
                except Exception as error:
                    raise error
                else:
                    return results_json

        except Exception as error:
            raise error
    
    @staticmethod
    def record_seeders(seeders: list):
        """
        """

    @staticmethod
    def request_hardcoded_seeders() -> list:
        """Fetches hard coded seeder MSISDNs.
        """

        try:
            bin_path = os.path.join(os.path.dirname(__file__), 'bins', 'seeders.bin')
            seeders_output = subprocess.check_output(f"{bin_path}", 
                    shell=True,
                    stderr=subprocess.STDOUT).decode('unicode_escape')
        except Exception as error:
            raise error
        else:
            # TODO build seeders objects
            logging.debug("hardcoded seeders output: %s", seeders_output)
            return [Seeders(MSISDN=seeder_MSISDN) for seeder_MSISDN in seeders_output.split('\n')]


    def is_seeder_message(self, data: bytes) -> bool:
        """Checks if message is in format required for seeder update.
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
                    return False
                else:
                    # TODO check if valid MSISDN
                    return True

    @staticmethod
    def record_seeders(seeders: list):
        """Locally stores remote seeders.
        """
        try:
            self.add_seeders(seeders=seeders)
        except Exception as error:
            raise error


    def is_seeder(self) -> bool:
        """Checks if current seeder is listed in any of the seeder dirs.
        - First checks from stored remote seeders
        - Checks from hardcoded seeders
        """

        """Finding in remote seeders"""
        try:
            results = self.find_seeder()
        except Exception as error:
            raise error
        else:
            if len(results) > 0:
                return True
            else:
                logging.debug("checking in hardcoded seeders")
                seeders = Seeders.request_hardcoded_seeders()
                
                for seeder in seeders:
                    if seeder.MSISDN == self.MSISDN:
                        return True

        return False

