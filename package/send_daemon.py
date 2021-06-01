#!/bin/python

import os
import threading
import subprocess
import start_routines
import logging
import time
import configparser
import deduce_isp as ISP

from libMMCLI_python.lsms import SMS 
from libMMCLI_python.lmodem import Modem 
from lmodems import Modems 
from datastore import Datastore

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')

if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
    exit()

format = "[%(asctime)s] >> %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")


def send_sms(modem, sms):
    datastore = Datastore()
    send_status=None
    try:
        messageLogID = datastore.new_log(messageID=sms.messageID)
    except Exception as error:
        raise( error )
    else:
        try:
            send_status=modem.send_sms( modem.set_sms(sms) )
            if send_status is None:
                logging.warning("[-] Send status failed with sys error")

            elif not send_status["state"]:
                logging.warning("[-] Failed to send...")
                datastore.release_message(messageID=sms.messageID, status="failed")
                modem.remove_sms(sms)
            else:
                logging.info("[+] Message sent!")
        except Exception as error:
            print("[+] Exception as:", error )
            raise Exception( error )
        else:
            datastore.update_log(messageLogID=messageLogID, status=send_status["status"], message=send_status["message"])
            print(">>send status:", send_status)
            return send_status["state"]


def claim(modem):
    try:
        datastore = Datastore()
        modem.extractInfo()
        isp = ISP.acquire_isp(operator_code=modem.details["modem.3gpp.operator-code"])
        # print("[+] Deduced ISP:", isp)
        router=False
        if "isp" in CONFIGS["ROUTER"] and CONFIGS["ROUTER"]["isp"] == isp:
            router=True
        # print("[+] ROUTER SET TO: ", router)
        new_message = datastore.acquire_message(modem_index=modem.index, modem_imei=modem.details["modem.3gpp.imei"], isp=isp, router=router)
    except Exception as error:
        raise Exception( error )
    else:
        if not new_message==None:
            sms = SMS(messageID=new_message["id"])
            sms.create_sms( phonenumber=new_message["phonenumber"], text=new_message["text"] )
            
            return sms
        else:
            return None

def daemon():
    print("NAME:", threading.current_thread())
    logging.info("[+] Write daemon begun...")
    # Beginning daemon from here
    modems = Modems()

    # check to make sure everything is set for takefoff
    try:
        prev_list_of_modems = []
        fl_no_modem_shown = False
        shownNoAvailableMessage=False

        threadCollections={}
        loopCounter = 1
        while loopCounter:
            # print(f"[+] LC {loopCounter}")
            loopCounter += 1

            list_of_modems = modems.get_modems()
            # logging.info(f"[+] Scanning for modems...")
            if len(list_of_modems) == 0:
                    if not fl_no_modem_shown:
                        logging.info("No modem found...")
                        fl_no_modem_shown = True

                    sleepTime = int(CONFIGS["MODEMS"]["sleep_time"])
                    time.sleep(sleepTime)
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

                # checks if the modem is currently trying to send out an SMS message
                if modem_imei in threadCollections:
                    if threadCollections[modem_imei].is_alive():
                        continue
                    else:
                        del threadCollections[modem_imei]
                try: 
                    sms = claim(modem)
                    if sms is not None and sms is not False:# claim updates messages and starts new log
                        print("[+] SMS message:", sms.text)
                        messageClaimed=True
                        shownNoAvailableMessage=False
                        logging.info(f"{modem_imei}::{modem.index} - Message claimed!")
                        
                        newThreadCollections[modem_imei]=threading.Thread( target=send_sms, args=(modem,sms,), daemon=True)
                except Exception as error:
                    logging.warning(error)

            # print(f"[+] Threaded: {len(newThreadCollections)} modems...")
            for modemIMEI in newThreadCollections:
                if modemIMEI in threadCollections:
                    if not threadCollections[modemIMEI].is_alive():
                        print("[=====] something is wrong here....")
                    continue

                elif not newThreadCollections[modemIMEI].is_alive():
                    newThreadCollections[modemIMEI].start()
                    threadCollections[modemIMEI] = newThreadCollections[modemIMEI]

            if not messageClaimed and not shownNoAvailableMessage:
                shownNoAvailableMessage=True
                logging.info(f"No available message...")

            prev_list_of_modems = list_of_modems
            sleepTime = int(CONFIGS["MODEMS"]["sleep_time"])
            time.sleep(sleepTime)
            # logging.info("[-] DONE SLEEPING....")
    except Exception as error:
        print( error)

if __name__ == "__main__":
    try:
        send_sms()
    except Exception as error:
        print( error )
