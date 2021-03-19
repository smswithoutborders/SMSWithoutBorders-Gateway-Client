#!/bin/python

import subprocess
import start_routines
import logging

from libs.lsms import SMS 
from libs.lmodem import Modem 
from libs.lmodems import Modems 

# Beginning daemon from here
modems = Modems()

# check to make sure everything is set for takefoff
print(">> Starting system diagnosis...")
try:
    check_state = start_routines.sr_database_checks()
    if not check_state:
        print("\t- Start routine check failed...")
except Exception as error:
    # print("Error raised:", error)
    print( error )
else:
    print("\t- All checks passed.... proceeding...")
    try:
        prev_list_of_modems = []
        fl_no_modem_shown = False

        format = "[%(asctime)s] >> %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

        while True:
            list_of_modems = modems.get_modems()
            if len(list_of_modems) == 0 and not fl_no_modem_shown:
                    logging.info("No modem found...")
                    fl_no_modem_shown = True
                    continue

            modemInstancesCollection=[]
            for modem_index in list_of_modems:
                fl_no_modem_shown = False

                modem = Modem( modems.datastore, modem_index )
                if not modem.ready_state():
                    continue

                if not modem_index in prev_list_of_modems:
                    logging.info(f"[+] New modem found: [{modem.info()[modem.operator_code]}:{modem_index}]")
                modemInstancesCollection.append( modem )


            for modem in modemInstancesCollection:
                try: 
                    if modem.claim()==None:# claim updates messages and starts new log
                        logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - No available message...")
                    else:
                        logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - Message claimed!")

                except Exception as error:
                    print( error )
                else:
                    # TODO: this should be threaded and detached if possible
                    # modem.send_sms() # updates counter for message and logs after sending
                    pass

            prev_list_of_modems = list_of_modems
    except Exception as error:
        print( error)
