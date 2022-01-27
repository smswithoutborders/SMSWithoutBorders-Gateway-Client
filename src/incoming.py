#!/usr/bin/env python3

import logging

from modem_manager import ModemManager
from models.gateway_incoming import NodeIncoming

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
        modemManager.add_model(model=NodeIncoming)
        # modemManager.daemon()
    except Exception as error:
        raise error

if __name__ == "__main__":
    main()
