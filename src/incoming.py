#!/usr/bin/env python3

import logging
import sqlite3

from modem_manager import ModemManager
from models.gateway_incoming import NodeIncoming
from ledger import Ledger

def main(modemManager:ModemManager)->None:
    """Starts listening for incoming messages.

        Args:
            ModemManager: An instantiated modemManager. Provide this to begin 
            monitoring modems for incoming messages.

        TODO:
            - Check ledger for seeders
                + if not exist:
                    - create one
            - Check ledger for self MSISDN and IMSI
                + if not exist:
                    - send request to default MSISDN for MSISDN for IMSI
    """
    logging.debug("Gateway incoming initializing...")

    try:
        ''' would creat the clients and seeders ledger '''
        ledger = Ledger(populate_tables=['clients'])
        logging.debug("ledgers checked and created")

    except sqlite3.OperationalError as error:
        logging.debug("ledger exist already")

    except Exception as error:
        raise error

    try:
        modemManager.add_model(model=NodeIncoming)
    except Exception as error:
        raise error

if __name__ == "__main__":
    main()
