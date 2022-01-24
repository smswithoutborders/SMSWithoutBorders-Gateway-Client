#!/usr/bin/env python3

import time 
import os
import pika
import socket
import threading
import traceback
import json
import requests
import logging
from datetime import datetime
from base64 import b64encode

from deku import Deku
from enum import Enum

from common.mmcli_python.modem import Modem
from router import Router
from remote_control import RemoteControl

from modem_manager import ModemManager
from models.gateway_incoming import NodeIncoming

def route_online(data):
    try:
        results = router.route_online(data=data)
        logging.info("routing results (online) %s %d", 
                results.text, results.status_code)
    except Exception as error:
        raise error

def route_offline(text, number):
    try:
        results = router.route_offline(text=text, number=number)
        logging.info("routing results (offline) successful")
    except Exception as error:
        raise error

def sms_routing_callback(ch, method, properties, body):
    logging.debug(body)
    json_body = json.loads(body.decode('unicode_escape'), strict=False)
    logging.info("routing %s", json_body)

    if not "text" in json_body:
        logging.error('poorly formed message - text missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    if not "phonenumber" in json_body:
        logging.error('poorly formed message - number missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        json_data = json.dumps(json_body)
        body = str(b64encode(body), 'unicode_escape')

        logging.debug("routing mode %s", router_mode)
        if router_mode == Router.Modes.ONLINE.value:
            route_online(json_data)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif router_mode == Router.Modes.OFFLINE.value:
            route_offline(body, router_phonenumber)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif router_mode == Router.Modes.SWITCH.value:
            try:
                route_online(json_data)
                routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as error:
                try:
                    route_offline(body, router_phonenumber)
                    routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as error:
                    raise error
        else:
            logging.error("invalid routing protocol")
    except Exception as error:
        logging.exception(traceback.format_exc())
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)



def rabbitmq_connection(config):
    connection_url=config['GATEWAY']['connection_url']
    queue_name=config['GATEWAY']['routing_queue_name']

    logging.info("attempting connection for %s (%s)", connection_url, queue_name)
    try:
        routing_consume_connection, routing_consume_channel = create_channel(
                connection_url=connection_url,
                callback=sms_routing_callback,
                durable=True,
                prefetch_count=1,
                queue_name=queue_name)

        # logging.info("connected to localhost")
        return routing_consume_connection, routing_consume_channel

    except Exception as error:
        raise error

def incoming_listener():
    deku=Deku(config=config, 
            config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    router_mode = config['GATEWAY']['route_mode']
    router_phonenumber = config['GATEWAY']['router_phonenumber']

    url = config['GATEWAY']['route_url']
    priority_offline_isp = config['GATEWAY']['route_isp']
    router = Router(url=url, priority_offline_isp=priority_offline_isp, 
            config=config, config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    try:
        routing_consume_connection, routing_consume_channel = rabbitmq_connection(config)

        routing_thread = threading.Thread(
                target=routing_consume_channel.start_consuming, daemon=True)

        # route listener begins here
        routing_thread.start()

        # if manage_modems dies - incoming listeners die
        """
        manage_modems(config, config_event_rules, 
                config_isp_default, config_isp_operators)
        """

    except pika.exceptions.ConnectionClosedByBroker as error:
        logging.critical(error)


def main(modemManager:ModemManager)->None:
    """Starts listening for incoming messages.
    """
    logging.debug("Gateway incoming initializing...")
    """
    try:
        if not setup_ledger():
            raise Exception('failed to setup ledger')
        
        if not setup_modem_manager():
            raise Exception('failed to setting up modem manager')
    except Exception as error:
        raise error
    """

    try:
        modemManager.add_model(model=NodeIncoming)
        modemManager.daemon()
    except Exception as error:
        raise error

if __name__ == "__main__":
    main()
