#!/usr/bin/env python3

import logging

from modem_manager import ModemManager
from models.node_outbounds import NodeOutbounds

def main(modemManager:ModemManager)->None:
    """Starts listening for incoming messages.

        Args:
            ModemManager: An instantiated modemManager. Provide this to begin 
            monitoring modems for incoming messages.
    """
    logging.debug("Gateway outgoing initializing...")

    """
    try:
        if not setup_ledger():
            raise Exception('failed to setup ledger')
        
        if not setup_modem_manager():
            raise Exception('failed to setting up modem manager')
    except Exception as error:
        raise error
    """

    try:
        modemManager.add_model(model=NodeOutbounds)
        # modemManager.daemon()
    except Exception as error:
        raise error

if __name__ == "__main__":
    main()
