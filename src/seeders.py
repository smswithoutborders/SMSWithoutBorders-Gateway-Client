#!/usr/bin/env python3

import os
import logging
import subprocess

class Seeders:
    def __init__(self, MSISDN: str=None, _id: str = None):
        self._id = _id
        self.MSISDN = MSISDN

    def update_state(self, state: str=None):
        """
        """

    @staticmethod
    def _filter(seeders: list, filters: dict) -> list:
        """
        """
        seeders = []
        return seeders

    @staticmethod
    def request_remote_seeders() -> list:
        """
        """
        seeders = []
        return seeders

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

