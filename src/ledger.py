#!/usr/bin/env python3

import logging

class Ledger:
    
    def __init__(self, IMSI):
        """Creates an instance of ledger for the IMSI (node).
        In case the ledger does not already exist, it is created.
        """
        self.IMSI = IMSI


        """
        Check if ledger file exist,
        if not, create it
        """

        try:
            if not self.__is_ledger_file__():
                try:
                    self.__create_ledger_file__()
                    logging.info("Created ledger for %s", self.IMSI)
                except Exception as error:
                    raise error
            else:
                logging.debug("Ledger exist for %s", self.IMSI)
        except Exception as error:
            raise error

    def __is_ledger_file__(self):
        return False

    def __create_ledger_file__(self):
        pass


    def find_seed(self):
        return False
