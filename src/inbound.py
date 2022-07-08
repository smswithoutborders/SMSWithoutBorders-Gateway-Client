#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time

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


def modem_connected_handler(modem: Modem) -> None:
    """
    """
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
