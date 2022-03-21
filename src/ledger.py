#!/usr/bin/env python3

import logging
import sqlite3 as database

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
        self.database_conn = None
        self.ledger_filename = os.path.join(
                os.path.dirname(__file__), '.db/nodes', f"{IMSI}.db")

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
        try:
            self.database_conn = database.connect(
                    f"file:{self.ledger_filename}.db?mode=rw", uri=True)
        except database.OperationalError as error:
            return False
        except Exception as error:
            raise error

        return True

    def __create_ledger_file__(self) -> None:
        """Create ledger file.
        """
        self.database_conn = database.connect(self.ledger_filename)

    def is_ledger(self) -> bool:
        """Checks if ledger file exist.
        """
        return self.__is_ledger_file__()
