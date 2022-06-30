#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import configparser
import logging 
import time
import json
import threading
import base64
import pika

from models.modem import Modem

from rabbitmq_broker import RabbitMQBroker
import helpers

class NodeInbound(threading.Event):
    locked_modems = True


    def __init__(self) -> None:
        """
        """
        super().__init__()

    def main(modem:Modem, **kwargs)->None:
        """
        """
        modem = modem
        daemon_sleep_time = 3
        configs = kwargs['configs']


    def handler_function_message_changed(*args, **kwargs) -> None:
        """
        """
        logging.debug("new message ready for publishing...")
        try:
            publish_connection, publish_channel = \
                    RabbitMQBroker.create_channel(
                        connection_url=publish_url,
                        connection_name='inbound_listener',
                        queue_name=queue_name,
                        heartbeat=600,
                        blocked_connection_timeout=60,
                        durable=True)
        except pika.exceptions.AMQPConnectionError as error:
            logging.error(error)

        else:
            text = None
            number = None
            publish_data = {"text":text, "MSISDN":number}

            try:
                publish_channel.basic_publish(
                        exchange='',
                        routing_key=queue_name,
                        body=json.dumps(publish_data),
                        properties=pika.BasicProperties(
                            delivery_mode=2))

                logging.debug("published %s", publish_data)
            except Exception as error:
                logging.exception(error)
            else:
                """
                """
                logging.debug("published: %s %s", text, number)
