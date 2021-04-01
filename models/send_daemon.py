#!/bin/python

import os
import threading
import subprocess
import start_routines
import logging
import time

from models.lsms import SMS 
from models.lmodem import Modem 
from models.lmodems import Modems 
        
import configparser
CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../configs', 'config.ini')

if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
    exit()

def daemon():
    # Beginning daemon from here
    modems = Modems()

    # check to make sure everything is set for takefoff
    format = "[%(asctime)s] >> %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
    try:
        prev_list_of_modems = []
        fl_no_modem_shown = False
        shownNoAvailableMessage=False


        threadCollections={}
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
                # logging.info(f"[+] Created modem instances")
                if not modem.readyState():
                    continue

                if not modem_index in prev_list_of_modems:
                    logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - Modem is ready!")
                    logging.info(f"New modem found: {modem.details['modem.3gpp.imei']}::{modem.index}")
                    modems.release_pending_messages(modem.extractInfo()["modem.3gpp.imei"])
                modemInstancesCollection.append( modem )


            messageClaimed=False
            newThreadCollections={}
            for modem in modemInstancesCollection: 
                modem_imei = modem.details["modem.3gpp.imei"]
                if modem_imei in threadCollections:
                    if threadCollections[modem_imei].is_alive():
                        # print("[+] Thread still active for modem:", modem_imei)
                        continue
                    else:
                        # print("[+] Thread is being released:", modem_imei)
                        del threadCollections[modem_imei]
                try: 
                    # logging.info(f"{modem.details['modem.3gpp.imei']}::{modem.index} - Claiming message!")
                    if modem.claim() is not None:# claim updates messages and starts new log
                        messageClaimed=True
                        shownNoAvailableMessage=False
                        # logging.info(f"text={modem.sms.text}\phonenumber={modem.sms.phonenumber})
                        logging.info(f"{modem_imei}::{modem.index} - Message claimed!")
                        
                        # threadCollections.append( threading.Thread( target=modem.send_sms, args=(modem.sms), daemon=True))
                        newThreadCollections[modem_imei]=threading.Thread( target=modem.send_sms, args=(modem.sms,))
                        # modem.send_sms( modem.sms ) # updates counter for message and logs after sending

                except Exception as error:
                    logging.warning(error)

            for m_imei in newThreadCollections:
                if m_imei in threadCollections:
                    continue
                '''
                    if not threadCollections[m_imei].is_alive():
                        del threadCollections[modem_imei]
                '''
                if not newThreadCollections[m_imei].is_alive():
                    # print(f"[+] starting:", m_imei, newThreadCollections[m_imei])
                    newThreadCollections[m_imei].start()
                    threadCollections[m_imei] = newThreadCollections[m_imei]
                    # print("[+]LEN:", len(threadCollections))

            if not messageClaimed and not shownNoAvailableMessage:
                shownNoAvailableMessage=True
                logging.info(f"No available message...")

            prev_list_of_modems = list_of_modems
            time.sleep( int(CONFIGS["MODEMS"]["sleep_time"]))
    except Exception as error:
        print( error)

if __name__ == "__main__":
    try:
        send_sms()
    except Exception as error:
        print( error )
