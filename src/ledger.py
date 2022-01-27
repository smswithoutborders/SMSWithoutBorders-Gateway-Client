#!/usr/bin/env python3

import os
import sqlite3
import logging
import traceback

class Ledger:
    def __init__(self, MSISDN:str=None, IMSI:str=None) -> None:
        self.con = None
        self.MSISDN = MSISDN
        self.IMSI = IMSI

        self.db_client_filepath = os.path.join(
                os.path.dirname(__file__), '.db', 'ledger.db')

        try:
            db_exist = self.__is_database__()
        except Exception as error:
            raise error

        if not db_exist:
            try:
                ''' options-
                1. create
                '''
                self.__create_db__()
                logging.debug('created db file')
            except Exception as error:
                raise error

            try:
                self.__create_db_tables__()
                logging.debug('tables created in db')

            except sqlite3.Warning as error:
                logging.warning(error)

            except Exception as error:
                raise error
        else:
            logging.debug('db file exist')

    def __create_db__(self):
        try:
            self.con = sqlite3.connect(self.db_client_filepath)
        except Exception as error:
            raise error
    
    def __create_db_tables__(self):
        try:
            cur = self.con.cursor()
            cur.execute('''CREATE TABLE clients
            (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            MSISDN TEXT NOT NULL UNIQUE,
            IMSI TEXT NOT NULL UNIQUE,
            update_platform TEXT NOT NULL,
            update_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL);''')
            
            self.con.commit()

        except sqlite3.Warning as error:
            # raise error
            logging.warning(error)

        except Exception as error:
            raise error

    def __is_database__(self):
        try:
            self.con = sqlite3.connect(
                    f"file:{self.db_client_filepath}?mode=rw",
                    uri=True)

        except sqlite3.OperationalError as error:
            # raise error
            return False
        except Exception as error:
            raise error

        return True

    def __read_clients_db__(self) -> list:
        cur = self.con.cursor()
        clients = list()

        try:
            for row in cur.execute(
                    'SELECT * FROM clients'):

                ''' database structure --- 

                + id:""
                + MSISDN:""
                + IMSI:""
                + update_platform:""
                + update_timestamp:""
                '''

                client = {}
                client['id'] = row[0]
                client['MSISDN'] = row[1]
                client['IMSI'] = row[2]
                client['update_platform'] = row[3]
                client['update_timestamp'] = row[4]

                clients.append(client)

        except sqlite3.Warning as error:
            logging.warning(error)

        except Exception as error:
            raise error

        return clients

    def get_list(self):
        try:
            clients = self.__read_clients_db__()
        except Exception as error:
            raise error

        return clients

    def create(self, data:dict) -> None:
        cur = self.con.cursor()
        data_values = (
                data['MSISDN'],
                data['IMSI'],
                data['update_platform'])

        try: 
            cur.execute("INSERT INTO clients( MSISDN, IMSI, update_platform) VALUES(?,?,?)", data_values)

            self.con.commit()

        except sqlite3.Warning as error:
            logging.warning(error)

        except Exception as error:
            raise error

    def exist(self, data:dict) -> bool:
        cur = self.con.cursor()
        
        try:
            rows = cur.execute(
                    "SELECT 1 FROM clients WHERE IMSI=:IMSI and MSISDN=:MSISDN",
                    {"IMSI":data['IMSI'], "MSISDN":data['MSISDN']}).fetchall()

            return True if rows[0][0] == 1 else False

        except sqlite3.Warning as error:
            logging.exception(error)

        except Exception as error:
            raise error

    def __del__(self):
        self.con.close()

if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    client = Clients()
