#!/usr/bin/env python3

import logging
import sqlite3

from modem_manager import ModemManager
from models.node_inbounds import NodeInbound
from ledger import Ledger

def main(modemManager:ModemManager)->None:
    """Starts listening for incoming messages.

        Args:
            ModemManager: An instantiated modemManager. Provide this to begin 
            monitoring modems for incoming messages.
    """
    logging.debug("Gateway incoming initializing...")

    try:
        modemManager.add_model(model=NodeInbound)
    except Exception as error:
        raise error

if __name__ == "__main__":
    main()
