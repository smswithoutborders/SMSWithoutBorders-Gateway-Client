#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time
import requests
from requests.exceptions import HTTPError

from modem_manager import ModemManager

from modem import Modem

from router import Router

from message_store import MessageStore

def new_message_handler(message, sim_imsi) -> None:
    """
    """
    text, number, timestamp = message.new_received_message()

    try:
        message_id = MessageStore().store(
                sim_imsi=sim_imsi, text=text, 
                number=number, timestamp=timestamp, _type='incoming')

    except Exception as error:
        logging.exception(error)
    else:
        logging.debug("Succesfully stored message: %d", message_id)

    logging.debug("\n\ttext:%s\n\tnumber:%s\n\ttimestamp:%s", text, number, timestamp)

    registration_requested = False

    standard_format_text = "%IMSI^^: "
    if text.find(standard_format_text) > -1:
        '''request from a seeder, requires registration'''
        text = text[len(standard_format_text):]
        registration_requested = True

    routing_urls = configs['NODES']['ROUTING_URLS']
    routing_urls = [url.strip() for url in routing_urls.split(',')]

    seeds_registration_urls = "https://developers.smswithoutborders.com:15000/seeds" if not 'SEEDS_REGISTRATION_URLS' in configs['NODES'] else configs['NODES']['SEEDS_REGISTRATION_URLS']
    seeds_registration_urls = [url.strip() for url in seeds_registration_urls.split(',')]

    try:
        if registration_requested:
            logging.debug("routing for registration...")
            router = Router(text=text, MSISDN=number, registration_urls=seeds_registration_urls)

        else:
            logging.debug("routing for publishing...")
            router = Router(text=text, MSISDN=number, routing_urls=routing_urls)

        try:
            if not registration_requested: 
                while message.messaging.modem.connected and not router.route():
                    time.sleep(2)
            else:
                while message.messaging.modem.connected and not router.register():
                    time.sleep(2)
        except HTTPError as error:
            logging.exception(error)
            code = error.response.status_code

            if code in [400, 401, 403]:
                message.messaging.messaging.Delete(message.message_path)
                logging.debug("deleted message: %s", message.message_path)
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


def search_local_seeds() -> list:
    """
    """
    logging.debug("searching for local seeds...")
    local_seeds = []
    local_seeds_filepath = os.path.join(os.path.dirname(__file__), '../records', f'local_seeds.json')

    with open(local_seeds_filepath, 'r') as fd:
        """
        """
        local_seeds = json.loads(fd.read())

    return local_seeds


def filter_seeds_for_best_match(modem: Modem, seeds: list) -> str:
    """
    """
    logging.debug("filtering seeds for best match")

    sim_operator_id = modem.get_3gpp_property("OperatorCode")
    logging.debug("Sim operator id: %s", sim_operator_id)

    for seed in seeds:
        if seed['IMSI'][:len(sim_operator_id)] == sim_operator_id:
            return seed['MSISDN']

    ''' return first seed if matching seeds not found '''
    return seeds[0]['MSISDN']

def request_sms_MSISDN(sim_imsi: str, sim_imsi_file: str, modem: Modem) -> None:
    """
    """
    logging.warning("Making SMS request for MSISDN")

    try:
        sim_imsi_sleep_file = sim_imsi_file.replace('.txt', '.sleep')
        seed_request_sleep_time = float(configs['NODES']['SEEDER_TIMEOUT'])
        seed_request_sleep_time = seed_request_sleep_time if seed_request_sleep_time > 300.0 else 300.0

        logging.debug("set sleep time to %d", seed_request_sleep_time)

        '''block sending multiple sms messages till scheduled sleep time '''
        if os.path.isfile(sim_imsi_sleep_file):
            with open(sim_imsi_sleep_file, 'r') as fd:
                data = fd.read()
                logging.debug("data: %s", data)
                start_sleep_epoch = float(data)

            current_epoch = time.time()
            end_sleep_epoch = start_sleep_epoch + seed_request_sleep_time

            if current_epoch < end_sleep_epoch:
                logging.debug("going to sleep for %d seconds", end_sleep_epoch - current_epoch)
                time.sleep(seed_request_sleep_time)

        if not os.path.isfile(sim_imsi_file):
            try:
                """Goal for this, get
                seeds number to send text"""

                gateway_server_url_seeds = configs['NODES']['SEEDS_PROBE_URLS']

                gateway_server_url_seeds = gateway_server_url_seeds.replace("/%s", '')

                response = requests.get(gateway_server_url_seeds, json={})

                response.raise_for_status()

                logging.debug("returned seeds: %s", response.text)

                response = response.json()

                if len(response) < 1:
                    response = search_local_seeds()
                    logging.debug("Local seeds: %s", response)

                    if len(response) < 1:
                        raise Exception("No sms seeds found!")

            except Exception as error:
                raise error

            else:
                try:
                    number = filter_seeds_for_best_match(modem, response)
                    text = "%%IMSI^^: %s" % (sim_imsi)

                    logging.debug("sending sms: %s, %s", number, text)
                    modem.messaging.send_sms( text=text, number=number)

                except Exception as error:
                    raise error

                finally:
                    with open(sim_imsi_sleep_file, 'w+') as fd:
                        fd.write(str(time.time()))
                    logging.debug("%s written", sim_imsi_sleep_file)

    except Exception as error:
        raise error


def request_MSISDN(sim_imsi: str, sim_imsi_file: str, modem: Modem) -> None:
    """
    """

    '''first check online if MSISDN for IMSI before going on with request'''

    gateway_server_url_seeds = configs['NODES']['SEEDS_PROBE_URLS'] % (sim_imsi)
    logging.debug("requesting msisdn from: %s", gateway_server_url_seeds)

    while modem.connected and not os.path.isfile(sim_imsi_file):
        response = requests.get(gateway_server_url_seeds)
        logging.debug("MSISDN response: %s, %s", response, response.text)

        if response.status_code == 200:
            if response.text == "":
                logging.warning("Nothing returned from server, probably failed to write on server")
                try:
                    request_sms_MSISDN(sim_imsi, sim_imsi_file, modem)
                except Exception as error:
                    logging.exception(error)

                else:
                    logging.debug("MSISDN sms request made for IMSI: %s", sim_imsi)

            else:
                '''write MSISDN to file'''
                # TODO: check if an actual MSISDN came back
                with open(sim_imsi_file, 'w+') as fd:
                    fd.write(response.text)

                logging.info("Created %s", sim_imsi_file)
                break

        elif response.status_code == 400:
            """
            """
            logging.debug("DB file not found on server... should make request to seeder")
            try:
                request_sms_MSISDN(sim_imsi, sim_imsi_file, modem)
            except Exception as error:
                logging.exception(error)

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
            time.sleep(10)

    logging.info("%s stopped making request for MSISDN", sim_imsi)


def modem_connected_handler(modem: Modem) -> None:
    """
    """
    if 'AUTO_ENABLE' in configs['NODES'] and int(configs['NODES']['AUTO_ENABLE'])== 1:
        try:
            modem.enable()
            logging.info("Modem auto enabled...")
        except Exception as error:
            logging.exception(error)


    print('after intiating line')

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

    if not MessageStore.has_store():
        MessageStore.create_store()

    modem_manager.add_modem_connected_handler(modem_connected_handler)
    logging.debug("Added modem connection handler...")
