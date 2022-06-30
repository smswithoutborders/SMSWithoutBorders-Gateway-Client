#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time
import pika

from modem_manager import ModemManager
from models.node_inbounds import NodeInbound
from router import Router
from rabbitmq_broker import RabbitMQBroker

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

        routing_urls = __configs['NODES']['routing_urls']
        routing_urls = [url.strip() for url in routing_urls.split(',')]

        try:
            requeue_message = False
            for i in range(len(routing_urls)):
                routing_url = routing_urls[i]

                logging.info("[*] routing %s: %s", json_body, routing_url)

                router = Router(url=routing_url)
                try:
                    router.route_online(data=json_body)

                except Router.NoInternetConnection as error:
                    logging.warn(
                    "** no internet connection... returning message to queue")

                    ch.basic_reject(
                            delivery_tag=method.delivery_tag, requeue=True)
                    requeue_message = True
                    break

                except Exception as error:
                    logging.exception(error)

        except Exception as error:
            logging.exception(error)
            ch.basic_reject(delivery_tag=method.delivery_tag)

        else:
            if not requeue_message:
                ch.basic_ack( delivery_tag=method.delivery_tag)

        finally:
            logging.debug("[*] sleeping for %d seconds", daemon_sleep_time)
            time.sleep(daemon_sleep_time)

def listen_for_routing_request(callback_function,
        publisher_connection_url: str = 'localhost',
        queue_name: str='inbound.route.route',
        route_url: str = 'localhost') -> None:
    """
    """
    logging.info("[*] Starting inbound routing listener...")

    try:
        router_connection, router_channel = RabbitMQBroker.create_channel( 
                connection_url=publisher_connection_url,
                connection_name="inbound_router",
                callback=callback_function,
                queue_name=queue_name)

        routing_request_thread = threading.Thread(
                target=router_channel.start_consuming, daemon=True)

        routing_request_thread.start()

    except pika.exceptions.ConnectionClosedByBroker as error:
        logging.exception(error)

def main(modemManager:ModemManager = None)->None:
    """Starts listening for incoming messages.

        Args:
            ModemManager: An instantiated modemManager. Provide this to begin 
            monitoring modems for incoming messages.
    """
    global __configs, daemon_sleep_time

    daemon_sleep_time = 10

    try:
        __configs = configparser.ConfigParser(interpolation=None)
        __configs.read(
                os.path.join(os.path.dirname(__file__), 
                    '../.configs', 'config.ini'))

        if modemManager:
            modemManager.add_model(model=NodeInbound, configs=__configs)

        try:
            routing_thread = threading.Thread(
                    target=listen_for_routing_request, 
                    args=(router_callback,),
                    daemon=True)
            # routing_thread.start()
        except Exception as error:
            logging.exception(error)

    except Exception as error:
        logging.exception(error)

if __name__ == "__main__":
    main()
