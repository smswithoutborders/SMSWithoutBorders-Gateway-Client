#!/usr/bin/env python3

import sys, os
import sqlite3
import logging
from common.mmcli_python.modem import Modem

class NodeIdentifier:
    def __init__(self, modem:Modem=None) -> None:
        # super().__init__()
        self.modem = modem
        self.ledger_filepath = os.path.join(
                os.path.dirname(__file__), '.db', 'ledger.db')

    def get_modem_imsi(self) -> str:
        try:
            sim_imsi = self.modem.get_sim_imsi()
            logging.debug('sim imsi: %s', sim_imsi)
            return sim_imsi
        except Exception as error:
            raise error
        return ""

    def __is_database__(self) -> None:
        try:
            self.con = sqlite3.connect(
                    f"file:{self.ledger_filepath}?mode=rw",
                    uri=True)

        except sqlite3.OperationalError as error:
            return False

        except Exception as error:
            raise error

        return True

    def __fetch_details__(self) -> dict:
        return []

    def ready(self) -> bool:
        """ requirements
        ledger_exist and MSIDN and ISMI:
            return True
        """
        try:
            if self.__is_database__():
                return True

        except Exception as error:
            raise error

        return False


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    modem_index = sys.argv[1]
    # n_id = NodeIdentifier(modem_index=modem_index)
    modem = Modem(index=modem_index)
    n_id = NodeIdentifier(modem)


    assert(n_id.get_modem_imsi() == "624017520955189")
    assert(n_id.ready() == True )
    ''' 
    * plan on getting listed - 
        - simcard checks self db for number
        - if number: 
            simcard is ready for making further request
        - if not number:
            simcard begins HANDSHAKE* to acquire number

    * syncing methodology - 
        - process
            -- SEEDER Gateway -- 
            + request BE API for account's hashed password
            + request BE API for account's stored platforms
                [{logo:"url", 
                short_letters:""},]


            -- APP -- 
            + request all GLOBALLY and LOCALLY available modems
                - GLOBALLY = general usage, configured in settings
                - LOCALLY = available just for country
                [gateways(obj),]

        - details transfered to synced app (encrypted with shared key)
            + account's hashed password
            + [platforms(obj),]
    
    * gateway acquisition methodology - 


    *HANDSHAKE:
    - simcard sends an SMS (sim_imsi) to a SEEDER Gateway (SG)
    - SG adds the incoming(number, sim_imsi) to its (DB - Distributd ledger)
    '''
