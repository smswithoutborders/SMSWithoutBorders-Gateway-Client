#!/usr/bin/env python3

import os
import logging
import sqlite3 as database

logging.basicConfig(level="DEBUG")

def list_databases() -> list:
    """
    """
    seeds = []

    database_filepaths = os.path.join(
            os.path.dirname(__file__), '../src/.db/nodes')

    for root, dirs, files in os.walk(database_filepaths):
        for file in files:
            if not file.endswith(".db"):
                continue
            db_filepath = "%s/%s" % (database_filepaths, file)

            seeds.append(db_filepath)
    return seeds

def show_database(database):
    """
    """
    # logging.debug("db_filepath: %s", db_filepath)
    database_conn = database.connect(database)

    cur = database_conn.cursor()
    try:
        cur.execute('''SELECT * FROM seeds''')
    except Exception as error:
        logging.exception(error)
    else:
        return cur.fetchall()


if __name__ == "__main__":
    """
    1. Check the status of seeds (see what's in the database)
    """

    databases = list_databases()

    for database in databases:
        seed_content = show_database(database)
        """
            seed[0][0] = IMSI
            seed[0][1] = MSISDN
            seed[0][2] = SEEDER_MSISDN
            seed[0][3] = state
            seed[0][4] = date (datetime)
        """
        logging.info("IMSI: %s", seed_content[0])
        logging.info("MSISDN: %s", seed_content[1])
        logging.info("SEEDER_MSISDN: %s", seed_content[2])
        logging.info("state: %s", seed_content[3])
        logging.info("date: %s\n", seed_content[4])
