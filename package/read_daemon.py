#!/bin/python

import os
import time
import logging
import requests
import traceback
import subprocess
import configparser
import deduce_isp as isp

from libMMCLI_python.lsms import SMS 
from libMMCLI_python.lmodem import Modem 
from lmodems import Modems 
from router import Router
from datastore import Datastore

format = "[%(asctime)s]>> %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
    
CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")

datastore = Datastore()

def route(mode, sms, modem=None):
    if mode == "online":
        logging.warning("ROUTING ONLINE MODE...")
        # router_url = DEKU_CONFIGS['router_url']
        router_url = CONFIGS["ROUTER"]["default"]
        router = Router(router_url)
        router_response = router.publish(sms)
        if router_response:
            logging.info("successfully routed!")
        else:
            logging.warning("routing failed!")
    elif mode == "offline":
        logging.warning("ROUTING OFFLINE MODE...")
        # logging.info("Moving to route to Twilio")
        # TODO: check if router is configured
        route_num=None
        if "router_phonenumber" in CONFIGS["ROUTER"]:
            route_num = CONFIGS["ROUTER"]["router_phonenumber"]
            datastore.new_message(text=sms.text, phonenumber=route_num, _type="routing", isp="")
        else:
            logging.warning("NO ROUTER NUM SET... MESSAGE WON'T BE ROUTED")

def daemon():
    logging.info("[+] Read daemon begun...")
    # format = "[%(asctime)s] [reading daemon]>> %(message)s"
    # logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    # Beginning daemon from here

    ROUTE = CONFIGS["ROUTER"]["route"]
    print(">> Starting system diagnosis...")

    modems = Modems()

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

        loopCounter=1
        while loopCounter:
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
                            logging.info(f"\n-Text: {sms.text}\n-Phonenumber: {sms.phonenumber}\n-Timestamp: {sms.timestamp}\n-Discharge Time: {sms.discharge_time}\n-State: {sms.state}")
                            datastore.new_message(text=sms.text, phonenumber=sms.phonenumber, _type=sms.state, isp='', claimed_modem_imei=modem.details["modem.3gpp.imei"])

                            if modem.remove_sms(sms):
                                logging.info(f"[-] SMS removed from modem")

                                # Routing if available
                                if ROUTE:
                                    if CONFIGS["ROUTER"]["offline_mode"] == "1":
                                        router_response = route(mode="offline", modem=modem, sms=sms)
                                        print( router_response )

                                    if CONFIGS["ROUTER"]["online_mode"] == "1":
                                        router_response = route(mode="online", sms=sms)
                                        print( router_response )

                                    if CONFIGS["ROUTER"]["offline_mode"] == "0" and CONFIGS["ROUTER"]["online_mode"] == "0":
                                        if Router.is_connected():
                                            route(mode="online", sms=sms)
                                        else:
                                            route(mode="offline", sms=sms, modem=modem)
                            else:
                                logging.warning(f">> Failed to remove SMS from modem")
                                exit() # TODO: DANGEROUS TO HAVE THIS EXCEPTION, MULTIPLE ROUTINGS WILL OCCUR 
                                raise Exception("Failed to remove SMS from modem")

                except Exception as error:
                    logging.warning(error)

            if not newReceivedMessage and not shownNoAvailableMessage:
                shownNoAvailableMessage=True
                logging.info(f"No received message...")

            prev_list_of_modems = list_of_modems
            sleepTime = int(CONFIGS["MODEMS"]["sleep_time"])
            time.sleep(sleepTime)
    except Exception as error:
        track = traceback.format_exc()
        # print("GLobal error: ", error)
        print(track)

if __name__ == "__main__":
    try:
        # Test routing - online
        data = ''
        sms = SMS()
        sms.timestamp = '2021-06-01T17:31:04+01:00'
        sms.text = 'aspjczo8dvgdyiyyVF2yf0pgLKGPSGfTkmj4Uryu+2BUzIkLblgtBG1nRH58oGEYDno6XvwagX0EVCZE9s6vZlYrAU0hgxWN6WnEbuTyt45pp3ARJZVmZBpRxXg='
        sms.phonenumber = '652156811'
        sms.isp = 'MTN'
        sms.state = 'received'
        route(mode='online', sms=sms)
    except Exception as error:
        print( error )
