#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time
import pika

from modem_manager import ModemManager
from modem import Modem, Messaging
from router import Router

def router_callback(ch, method, properties, body: bytes) -> None:
    """
    """
    try:
        decoded_body = body.decode('unicode_escape')
        json_body = json.loads(decoded_body, strict=False)

    except exception as error:
        """this most likely is not a request -> cus how did it get here if not json?"""
        logging.exception(error)

    else:
        if not "text" in json_body:
            """this most likely is not a request.
            -> cus how did it get here if not contain text?"""

            logging.error('poorly formed message - text missing')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        if not "MSISDN" in json_body:
            """this most likely is not a request. 
            -> cus how did it get here if not contain phone number?"""

            logging.error('poorly formed message - number missing')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return


def route_incoming_message(routing_urls: [], text: str, MSISDN: str) -> bool:
    """
    """
    try:
        my_fault_cannot_route = False # keep message if True
        for i in range(len(routing_urls)):
            routing_url = routing_urls[i]
            logging.debug("routing to: %s", routing_url)

            router = Router(url=routing_url)

            try:
                json_body = json.dumps({"text":text, "MSISDN":MSISDN})
                router.route_online(data=json_body)

            except Router.NoInternetConnection as error:
                logging.warn(
                "** no internet connection... returning message to queue")
                my_fault_cannot_route = True
                break

            except Exception as error:
                logging.exception(error)

    except Exception as error:
        logging.exception(error)

    else:
        if my_fault_cannot_route:
            return False

    return True

def get_signature(plain: str) -> str:
    """
    """
    try:
        import hashlib

        hashed = hashlib.md5(bytes(plain, 'utf-8')).hexdigest()
    except Exception as error:
        raise error
    else:
        return hashed


def new_message_handler(message: Messaging) -> None:
    """
    """
    text, number, timestamp = message.new_received_message()
    logging.debug("text:%s\n\tnumber:%s\n\ttimestamp:%s", text, number, timestamp)

    """
    Make each message unique
    """
    try:
        signature = timestamp + text + number
        signature = get_signature(signature)
        logging.debug("signature: %s", signature)
    except Exception as error:
        logging.exception(error)

    # routing_urls = configs['NODES']['routing_urls']
    routing_urls = "http://staging.smswithoutborders.com,https://staging.smswithoutborders.com"
    routing_urls = [url.strip() for url in routing_urls.split(',')]

    try:
        while not route_incoming_message(text=text, MSISDN=number, routing_urls=routing_urls):
            """
            """
            logging.debug("keeping message to try again later: %s", message.message_path)

            time.sleep(10)

        # TODO delete message
        logging.debug("deleting message: %s", message.message_path)
        
    except Exception as error:
        logging.exception(error)


def modem_connected_handler(modem: Modem) -> None:
    """
    """
    logging.debug("INBOUND: %s", modem)

    modem.add_new_message_handler(new_message_handler)


def main(modemManager:ModemManager = None, *args)->None:
    """
    """
    modemManager.add_modem_connected_handler(modem_connected_handler)
