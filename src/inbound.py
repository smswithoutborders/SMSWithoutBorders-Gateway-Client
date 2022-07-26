#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time
import requests

from modem_manager import ModemManager

from modem import Modem

from router import Router

def new_message_handler(message) -> None:
    """
    """
    text, number, timestamp = message.new_received_message()
    logging.debug("\n\ttext:%s\n\tnumber:%s\n\ttimestamp:%s", text, number, timestamp)

    routing_urls = configs['NODES']['ROUTING_URLS']
    routing_urls = [url.strip() for url in routing_urls.split(',')]

    try:
        router = Router(text=text, MSISDN=number, routing_urls=routing_urls)

        try:
            while message.messaging.modem.connected and not router.route():
                time.sleep(2)
        except Exception as error:
            logging.exception(error)
        else:
            try:
                message.messaging.messaging.Delete(message.message_path)
                logging.debug("deleted message: %s", message.message_path)
            except Exception as error:
                logging.exception(error)
        
    except Exception as error:
        logging.exception(error)


def modem_alive_ping(modem: Modem, 
        ping_urls: list = [], 
        ping_sleep_time: int = 10) -> None:
    """
    Ping data = IMSI.
    """
    while modem.connected:
        try:
            sim = modem.get_sim()
        except Exception as error:
            logging.exception(error)
        else:
            try:
                sim_imsi = sim.get_property("Imsi")
                sim_id = sim.get_property("SimIdentifier")
                operator_id = sim.get_property("OperatorIdentifier")

            except Exception as error:
                logging.exception(error)
            else:
                headers = {"sim_data":"%s.%s.%s" % (sim_imsi, operator_id, sim_id)}
                for url in ping_urls:
                    response = requests.get(url, headers=headers)
                    logging.debug("ping response: %s -> %s", url, response)

        time.sleep(ping_sleep_time)


def modem_connected_handler(modem: Modem) -> None:
    """
    """
    if 'AUTO_ENABLE' in configs['NODES'] and int(configs['NODES']['AUTO_ENABLE'])== 1:
        try:
            modem.enable()
            logging.info("Modem auto enabled...")
        except Exception as error:
            logging.exception(error)

    '''pinging session begins from here'''
    ping_urls = configs['NODES']['SEED_PING_URLS']
    ping_sleep_time = 10

    if 'ALIVE_PING_SLEEP_TIME' in configs['NODES']:
        ping_sleep_time = int(configs['NODES']['ALIVE_PING_SLEEP_TIME'])
        ping_sleep_time = 10 if ping_sleep_time < 10 else ping_sleep_time

    ping_urls = [url.strip() for url in ping_urls.split(',')]
    thread_ping_alive = threading.Thread(target=modem_alive_ping,
            args=(modem, ping_urls, ping_sleep_time), daemon=True)

    thread_ping_alive.start()
    logging.info("Started keep-alive ping sessions")

    modem.messaging.add_new_message_handler(new_message_handler)

    """
    modem.is_ready(): because signals won't be received if program restarts while modem
    is already plugged in. So check for ready modem message queues
    """
    if modem.is_ready():
        modem.messaging.check_available_messages()


def Main(modem_manager:ModemManager = None, *args, **kwargs)->None:
    """
    """
    global configs
    configs = kwargs['configs']

    modem_manager.add_modem_connected_handler(modem_connected_handler)
