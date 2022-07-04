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


    # routing_urls = configs['NODES']['routing_urls']
    routing_urls = "https://developers.smswithoutborders.com:15000/sms/platform/gateway-client"
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
    logging.debug("INBOUND: %s", modem)


    # TODO check for available messages from here
    # TODO add check for available messages on modem ready state changes

    modem.messaging.add_new_message_handler(new_message_handler)
    if modem.is_ready():
        modem.messaging.check_available_messages()


def main(modem_manager:ModemManager = None, *args, **kargs)->None:
    """
    """
    modem_manager.add_modem_connected_handler(modem_connected_handler)
