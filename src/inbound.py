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
    Ping data = IMSI.SimID
    """
    while modem.connected:
        try:
            sim = modem.get_sim()
        except Exception as error:
            logging.exception(error)
        else:
            try:
                sim_imsi = sim.get_property("Imsi")
            except Exception as error:
                logging.exception(error)

            else:
                headers = {"sim_data":"%s" % (sim_imsi)}
                for url in ping_urls:
                    try:
                        response = requests.get(url, headers=headers)
                    except requests.ConnectionError as error:
                        logging.error(error)
                    except Exception as error:
                        logging.exception(error)
                    else:
                        logging.debug("ping response: %s -> %s", url, response)

        time.sleep(ping_sleep_time)


def initiate_ping_sessions(modem: Modem) -> None:
    """Pinging session begins from here
    """
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

def request_MSISDN(sim_imsi: str, sim_imsi_file: str, modem: Modem) -> None:
    """
    """

    '''first check online if MSISDN for IMSI before going on with request'''

    gateway_server_url_seeds = configs['NODES']['SEEDS_PROBE_URLS'] % (sim_imsi)
    sim_imsi_sleep_file = sim_imsi_file.replace('.txt', '.sleep')
    seed_request_sleep_time = float(configs['NODES']['SEEDER_TIMEOUT'])
    seed_request_sleep_time = seed_request_sleep_time if seed_request_sleep_time > 300.0 else 300.0

    logging.debug("set sleep time to %d", seed_request_sleep_time)

    response = requests.get(gateway_server_url_seeds, json={'imsi':sim_imsi})

    logging.debug("MSISDN response: %s, %s", response, response.text)

    while modem.connected and not os.path.isfile(sim_imsi_file):
        if response.status_code == 200:
            # TODO: check the actual response from the server
            if response.text == "":
                request_MSISDN()

            else:
                with open(sim_imsi_file, 'w+') as fd:
                    fd.write(response)
                    logging.info("Created %s", sim_imsi_file)
                    break

        elif response.status_code == 400:
            """
            """
            logging.error(response.text)
            # TODO: make request for SMS
            try:
                if os.path.isfile(sim_imsi_sleep_file):
                    with open(sim_imsi_sleep_file, 'r') as fd:
                        start_sleep_epoch = float(fd.read())

                    current_epoch = time.time()
                    end_sleep_epoch = start_sleep_epoch + seed_request_sleep_time
                    if current_epoch < end_sleep_epoch:
                        logging.debug("going to sleep for %d seconds", end_sleep_epoch - current_epoch)
                        time.sleep(seed_request_sleep_time)
                        continue

                # TODO: if there's a sleep ongoing, resume it
                # self.modem.messaging.send_sms( text=text, number=number)
                raise Exception("")

            except Exception as error:
                logging.exception(error)

                with open(sim_imsi_sleep_file, 'w+') as fd:
                    fd.write(time.time())
                    logging.debug("%s written for %s", sim_imsi_sleep_file, sim_imsi)

            else:
                logging.debug("MSISDN sms request made for IMSI: %s", sim_imsi)
                break

        elif response.status_code == 404:
            """
            """
            logging.error(response.text)
            logging.warning("Breaking because url cannot be found, check url and restart service")
            break

        else:
            '''
            Most likely the server is down, sleep and try again
            '''
            # TODO: make time bigger to avoid overloading server
            time.sleep(2)

    logging.info("%s stopped making request for MSISDN", sim_imsi)

def initiate_msisdn_check_sessions(modem: Modem) -> None:
    """
    - Requires the IMSI.txt
    """
    logging.debug("Initiating MSISDN session checks")
    try:
        sim = modem.get_sim()
    except Exception as error:
        logging.exception(error)
    else:
        try:
            sim_imsi = sim.get_property("Imsi")

        except Exception as error:
            logging.exception(error)

        else:
            sim_imsi_file = os.path.join(os.path.dirname(__file__), '../records', f'{sim_imsi}.txt')
            logging.debug("IMSI file: %s", sim_imsi_file)

            if not os.path.isfile(sim_imsi_file) or os.path.getsize(sim_imsi_file) < 1:
                logging.warning("%s not found! should make request", sim_imsi_file)
                request_msisdn_thread = threading.Thread(target=request_MSISDN, 
                        args=(sim_imsi, sim_imsi_file, modem, ), daemon=True)

                request_msisdn_thread.start()
            else:
                logging.info("data file found for %s", sim_imsi_file)


def modem_connected_handler(modem: Modem) -> None:
    """
    """
    if 'AUTO_ENABLE' in configs['NODES'] and int(configs['NODES']['AUTO_ENABLE'])== 1:
        try:
            modem.enable()
            logging.info("Modem auto enabled...")
        except Exception as error:
            logging.exception(error)

    initiate_ping_sessions(modem)
    initiate_msisdn_check_sessions(modem)

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
