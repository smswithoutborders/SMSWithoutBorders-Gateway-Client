#!/bin/python

import os
import time
import logging
import requests
import traceback
import subprocess
import configparser
import deduce_isp as isp

from models.lsms import SMS 
from models.lmodem import Modem 
from models.lmodems import Modems 
from models.router import Router

format = "[%(asctime)s]>> %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
    
CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../configs', 'config.ini')
if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")

def daemon():
    logging.info("[+] Read daemon begun...")
    # format = "[%(asctime)s] [reading daemon]>> %(message)s"
    # logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    # Beginning daemon from here

    ROUTE = CONFIGS["ROUTER"]["route"]
    print(">> Starting system diagnosis...")

    modems = Modems()
    DEKU_CONFIGS = None
    try:
        DEKU_CONFIGS = modems.get_deku_configs()[0]
    except Exception as error:
        print(">> Check if configs have been enabled, could get not them from database")
        print(error)

    print("\t- All checks passed.... proceeding...")
    try:
        prev_list_of_modems = []
        fl_no_modem_shown = False
        shownNoAvailableMessage=False

        # Change route values
        if ROUTE == "1": # on
            ROUTE = True
            logging.info("Routing on")
        else: # off
            ROUTE = False
            logging.info("Routing off")

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

                modem = Modem(index=modem_index)

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
                            sms.phonenumber = isp.rm_country_code(sms.phonenumber)
                            # _isp = isp.deduce_isp( sms.phonenumber )
                            logging.info(f"\n\ttext>> {sms.text}\n\tphonenumber>> {sms.phonenumber}\n\ttimestamp>> {sms.timestamp}\n\tdischarge timestamp>> {sms.discharge_time}\n\tstate>> {sms.state}")
                            modem.new_message(text=sms.text, phonenumber=sms.phonenumber, _type=sms.state, isp='', claimed_modem_imei=modem.details["modem.3gpp.imei"])

                            if modem.remove_sms(sms):
                                logging.info(f"[-] SMS removed from modem")

                                # Routing if available
                                if ROUTE:
                                    if Router.is_connected() and not CONFIGS["ROUTER"]["offline_mode"] == "1":
                                        logging.warning("ACTIVE INTERNET CONNECTION...")
                                        router_url = DEKU_CONFIGS['router_url']
                                        router = Router(router_url)
                                        router_response = router.publish(sms)
                                        print( router_response )
                                    else:
                                        logging.warning("ROUTING OFFLINE MODE")
                                        logging.info("Moving to route to Twilio")

                                        # TODO: check if router is configured
                                        route_num=None
                                        if "router_phonenumber" in CONFIGS["ROUTER"]:
                                            route_num = CONFIGS["ROUTER"]["router_phonenumber"]
                                            modem.new_message(text=sms.text, phonenumber=route_num, _type="routing", isp="")
                                        else:
                                            logging.warning("NO ROUTER NUM SET... MESSAGE WON'T BE ROUTED")
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

if __name__ == "__main__":
    try:
        read_sms()
    except Exception as error:
        print( error )
