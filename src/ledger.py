#!/usr/bin/env python3

import os
import sqlite3
import logging
import traceback

class Ledger:
    def __init__(self, db_name:str=None, populate_tables:list=[], populate:bool=True) -> None:
        self.con = None
        self.db_name = db_name
        self.seeders = [
                # { "MSISDN":"+237671333468", "type":"swob-gateway-cluster" },
                { "MSISDN":"+237652156811", "type":"swob-gateway-cluster" },
                { "MSISDN":"+16073035353", "type":"twilio" }

                ]

        self.ledger_filepath = os.path.join(
                os.path.dirname(__file__), '.db', 'ledger.db')

        try:
            ledger_exist = self.__is_ledger_exist__()
        except Exception as error:
            raise error

        if not ledger_exist:
            try:
                self.__create_ledger__()
                logging.debug('ledger created successfully')

                self.__create_db_table__('seeders')
                logging.debug('seeder tables created')
                
                for seeder in self.seeders:
                    try:
                        self.insert_seeder_record(data=seeder)
                        logging.debug("insert new seeder record: %s", seeder)
                    except sqlite3.Warning as error:
                        logging.warning(error)
                    except Exception as error:
                        raise error

            except Exception as error:
                raise error

        else:
            logging.debug('ledger exist')

        if populate:
            for table in populate_tables:
                try:
                    self.__create_db_table__(table)
                    logging.debug('%s table created', table)
                except sqlite3.Warning as error:
                    logging.warning(error)

                except Exception as error:
                    raise error

    def __create_ledger__(self):
        try:
            self.con = sqlite3.connect(self.ledger_filepath)
        except Exception as error:
            raise error
    
    def __create_db_table__(self, table:str):
        tables = {
                "clients" : 
                '''CREATE TABLE clients 
                (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                MSISDN TEXT NOT NULL UNIQUE,
                IMSI TEXT NOT NULL UNIQUE,
                update_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL);''',

                "seeders" : 
                '''CREATE TABLE seeders 
                (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                MSISDN TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                state TEXT,
                update_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL);'''

                }


        if not table in tables:
            logging.error("request to create invalid table %s", table)
            raise Exception("unknown table")

        try:
            cur = self.con.cursor()
            cur.execute(tables[table])
            
            self.con.commit()

        except sqlite3.Warning as error:
            # raise error
            logging.warning(error)

        except Exception as error:
            raise error

    def __is_ledger_exist__(self):
        try:
            self.con = sqlite3.connect(
                    f"file:{self.ledger_filepath}?mode=rw",
                    uri=True)

        except sqlite3.OperationalError as error:
            return False

        except Exception as error:
            raise error

        return True

    def insert_seeder_record(self, data:dict) -> None:
        cur = self.con.cursor()
        data_values = (
                data['MSISDN'],
                data['type'])

        try: 
            cur.execute("INSERT INTO seeders ( MSISDN, type ) VALUES(?,?)", data_values)
            self.con.commit()

        except sqlite3.Warning as error:
            logging.warning(error)

        except Exception as error:
            raise error

    def insert_client_record(self, data:dict) -> None:
        cur = self.con.cursor()
        data_values = (
                data['MSISDN'],
                data['IMSI'])

        try: 
            cur.execute("INSERT INTO clients ( MSISDN, IMSI) VALUES(?,?)", data_values)
            self.con.commit()

        except sqlite3.Warning as error:
            logging.warning(error)

        except Exception as error:
            raise error

    def seeder_record_exist(self, data:dict) -> bool:
        cur = self.con.cursor()
        
        try:
            rows = cur.execute(
                    "SELECT 1 FROM seeders WHERE MSISDN=:MSISDN",
                    {"MSISDN":data['MSISDN']}).fetchall()

            return True if len(rows) > 0 and rows[0][0] == 1 else False

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error:
            raise error

    def client_record_exist(self, data:dict) -> bool:
        cur = self.con.cursor()
        
        try:
            rows = cur.execute(
                    "SELECT 1 FROM clients WHERE IMSI=:IMSI",
                    {"IMSI":data['IMSI']}).fetchall()

            return True if len(rows) > 0 and rows[0][0] == 1 else False

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error:
            raise error

    def get_records(self, table:str) -> None:
        cur = self.con.cursor()
        try:
            rows = cur.execute(
                    "SELECT ID, MSISDN FROM {} ORDER BY ID ASC".format(table)).fetchall()

            data = {}
            for index in range(len(rows)):
                row = rows[index]
                data[index] = {"MSISDN":row[1]}

            return data

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error:
            raise error

    def request_state(self, MSISDN:str)->None:
        cur = self.con.cursor()
        
        try:
            rows = cur.execute(
                    "SELECT MSISDN, state FROM seeders WHERE MSISDN=:MSISDN",
                    {"MSISDN":MSISDN}).fetchall()

            return '' if len(rows) < 1 else rows[0][1]

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error: raise error

    def update_seeder_state(self, state:str, MSISDN:str) ->None:
        cur = self.con.cursor()
        data_values = (state, MSISDN)

        try: 
            cur.execute("UPDATE seeders SET state=:state WHERE MSISDN=:MSISDN", 
                    {"state":state, "MSISDN":MSISDN})
            self.con.commit()

        except sqlite3.Warning as error:
            logging.warning(error)

        except Exception as error:
            raise error

    def get_seeder(self, MSISDN:str)->None:
        cur = self.con.cursor()
        
        try:
            rows = cur.execute(
                    "SELECT * FROM seeders WHERE MSISDN=:MSISDN",
                    {"MSISDN":MSISDN}).fetchall()

            return rows

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error: raise error


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    client = Clients()
