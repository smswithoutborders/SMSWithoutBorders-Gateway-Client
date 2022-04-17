#!/usr/bin/env python3

import os
import logging
import time
import sqlite3 as database

class Ledger:
    
    def __init__(self, IMSI: str=None, MSISDN: str=None):
        """Creates an instance of ledger for the IMSI (node).
        In case the ledger does not already exist, it is created.
        """
        self.IMSI = IMSI
        self.MSISDN = MSISDN

        """
        Check if ledger file exist,
        if not, create it
        """
        self.database_conn = None

        if IMSI:
            self.seeds_ledger_filename = os.path.join(
                    os.path.dirname(__file__), '.db/nodes', f"{IMSI}.db")

            try:
                if not self.__is_ledger_file__(self.seeds_ledger_filename):
                    try:
                        self.__create_seeds_ledger_file__()
                        logging.info("Created seed's ledger for %s", self.IMSI)

                        self.__populate_seed_ledger_file__()
                        logging.info("Populated seed ledger for %s", self.IMSI)
                    except Exception as error:
                        raise error
                else:
                    logging.debug("Ledger exist for %s", self.IMSI)
            except Exception as error:
                raise error

        if MSISDN:
            self.seeders_ledger_filename = os.path.join(
                    os.path.dirname(__file__), '.db/seeders', f"remote_seeders.db")

            try:
                if not self.__is_ledger_file__(self.seeders_ledger_filename):
                    try:
                        self.__create_seeders_ledger_file__()
                        logging.info("Created seeders ledger for %s", self.IMSI)
                    except Exception as error:
                        raise error
                else:
                    logging.debug("Ledger exist for seeders")
            except Exception as error:
                raise error

    def __is_ledger_file__(self, ledger_filename: str) -> bool:
        """Checks if ledger file exist.
        """
        try:
            self.database_conn = database.connect(
                    f"file:{ledger_filename}?mode=rw", uri=True)
        except database.OperationalError as error:
            return False
        except Exception as error:
            raise error

        return True

    def is_ledger(self) -> bool:
        """Checks if ledger file exist.
        """
        return self.__is_ledger_file__()

    def __create_seeds_ledger_file__(self) -> None:
        """Create ledger file.
        """
        self.database_conn = database.connect(self.seeds_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.execute( f'''
            CREATE TABLE seed
            (IMSI text NOT NULL, 
            MSISDN text, 
            SEEDER_MSISDN text, 
            state text,
            state_time text,
            date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL) ''')
            self.database_conn.commit()
        except Exception as error:
            raise error
    
    def __populate_seed_ledger_file__(self)->None:
        database_conn = database.connect(self.seeds_ledger_filename)

        cur = database_conn.cursor()
        try:
            cur.execute(f"INSERT INTO seed VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))", 
                    (self.IMSI, None, None, None, None))
            database_conn.commit()
        except Exception as error:
            raise error

    def __create_seeders_ledger_file__(self) -> None:
        """Create ledger file.
        """
        self.database_conn = database.connect(self.seeders_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.execute( f'''
            CREATE TABLE seeders
            (MSISDN text PRIMARY KEY, 
            date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL);
            ''')
            self.database_conn.commit()
        except Exception as error:
            raise error

    def find_seed_record(self) -> list:
        """Finds the fields
            seed[0][0] = IMSI
            seed[0][1] = MSISDN
            seed[0][2] = SEEDER_MSISDN
            seed[0][3] = state
            seed[0][4] = date (datetime)
        """
        database_conn = database.connect(self.seeds_ledger_filename)
        cur = database_conn.cursor()

        try:
            """Because there will always be just one seed. More than one seed and there's a problem"""
            cur.execute('''SELECT * FROM seed''')
        except Exception as error:
            raise error
        else:
            return cur.fetchall()

    
    def find_seed(self) -> list:
        """Finds the fields when MSISDN is not NULL
            seed[0][0] = IMSI
            seed[0][1] = MSISDN
            seed[0][2] = SEEDER_MSISDN
            seed[0][3] = state
            seed[0][4] = date (datetime)
        """
        self.database_conn = database.connect(self.seeds_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            """Because there will always be just one seed. More than one seed and there's a problem"""
            cur.execute('''SELECT * FROM seed WHERE MSISDN IS NOT NULL''')
        except Exception as error:
            raise error
        else:
            return cur.fetchall()

    def find_seeder(self) -> list:
        """Finds the fields
        """
        self.database_conn = database.connect(self.seeders_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.execute('''SELECT * FROM seeders WHERE MSISDN=:MSISDN''', {"MSISDN":self.MSISDN})
        except Exception as error:
            raise error
        else:
            return cur.fetchall()

    def update_seed_MSISDN(self, seed_MSISDN: str):
        """
        """

        self.database_conn = database.connect(self.seeds_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.execute('''UPDATE seed SET MSISDN=:MSISDN WHERE IMSI=:IMSI''', 
                    {"MSISDN":seed_MSISDN, "IMSI":self.IMSI})
            self.database_conn.commit()
        except Exception as error:
            raise error
        else:
            return cur.rowcount

    def update_seed_state(self, seeder_MSISDN: str, state: str):
        """Changes the state of the request for the seed.
        Seeds states can either be:
            - NULL
            - Requested
            - Confirmed
        """
        database_conn = database.connect(self.seeds_ledger_filename)

        cur = database_conn.cursor()
        try:
            state_time = str(time.time())

            cur.execute(''' UPDATE seed SET 
                    state=:state, 
                    SEEDER_MSISDN=:seeder_MSISDN, 
                    state_time=:state_time 
                    WHERE IMSI=:IMSI''', 
                    {"state":state, "seeder_MSISDN":seeder_MSISDN, "state_time":state_time, "IMSI":self.IMSI})

            database_conn.commit()
        except Exception as error:
            raise error
        else:
            return cur.rowcount

    def update_seeds_seeder_MSISDN(self, seeder_MSISDN: str):
        """
        """

        self.database_conn = database.connect(self.seeds_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.execute('''UPDATE seed SET seeder_MSISDN=:seeder_MSISDN''', {"seeder_MSISDN":seeder_MSISDN})
            self.database_conn.commit()
        except Exception as error:
            raise error


    @staticmethod
    def add_seeders(seeders: list):
        """
        """

        self.database_conn = database.connect(self.seeders_ledger_filename)

        cur = self.database_conn.cursor()
        try:
            cur.executemany('''INSERT INTO seeders values (?)''', 
                    [("MSISDN", seeder.MSISDN) for seeder in seeders])
        except Exception as error:
            raise error
        else:
            return cur.fetchall()

