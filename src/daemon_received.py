#!/bin/python

import subprocess
import start_routines
import logging
import time
import traceback

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
        shownNoAvailableMessage=False

        format = "[%(asctime)s] >> %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

        while True:
            list_of_modems = modems.get_modems()
            # logging.info(f"[+] Scanning for modems...")
            if len(list_of_modems) == 0 and not fl_no_modem_shown:
                    logging.info("No modem found...")
                    fl_no_modem_shown = True
                    continue

            modemInstancesCollection=[]
            for modem_index in list_of_modems:
                fl_no_modem_shown = False

                modem = Modem(index=modem_index )

                if not modem_index in prev_list_of_modems:
                    logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - Modem is ready!")
                    logging.info(f"New modem found: {modem.details['modem.3gpp.imei']}::{modem.index}")
                modemInstancesCollection.append( modem )


            newReceivedMessage=False
            for modem in modemInstancesCollection:
                try: 
                    # logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - Claiming message!")
                    messages = modem.get_received_messages()
                    if len(messages) > 0:
                        newReceivedMessage=True
                        shownNoAvailableMessage=False
                        logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - New Message Found!")
                        for sms in messages:
                            logging.info(f"[+] Reading new messages...")
                            logging.info(f"\n\ttext>> {sms.text}\n\tphonenumber>> {sms.phonenumber}\n\ttimestamp>> {sms.timestamp}\n\tdischarge timestamp>> {sms.discharge_time}\n\tstate>> {sms.state}")
                            # It's just to store and then get rid of them from the modems
                            modem.new_message(text=sms.text, phonenumber=sms.phonenumber, _type=sms.state, isp="")
                            if modem.remove_sms(sms):
                                logging.info(f"[-] SMS removed from modem")
                            else:
                                logging.warning(f">> Failed to remove SMS from modem")
                                raise Exception("Failed to remove SMS from modem")

                except Exception as error:
                    logging.warning(error)

            if not newReceivedMessage and not shownNoAvailableMessage:
                shownNoAvailableMessage=True
                logging.info(f"No received message...")

            prev_list_of_modems = list_of_modems
            time.sleep(3)
    except Exception as error:
        track = traceback.format_exc()
        # print("GLobal error: ", error)
        print(track)
