#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import threading
import subprocess
import json
import time
import pika 
import configparser
import logging
import phonenumbers

from enum import Enum

from deku import Deku
from common.mmcli_python.modem import Modem
from rabbitmq_broker import RabbitMQBroker

'''
resources:
    - https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html?highlight=BlockingChannel#pika.adapters.blocking_connection.BlockingChannel
'''

class NodeOutgoing(threading.Event):

    @staticmethod
    def init(modem:Modem, daemon_sleep_time:int=3)->NodeOutgoing:
        """Create an instance of :cls:NodeOutgoing.

            Args:
                modem: Instanstiates a node for this modem.
                daemon_sleep_time: Sleep time for each modem.
                active_nodes: from :cls:ModemManager to manage active nodes.
        """

        nodeOutgoing = NodeOutgoing(modem, daemon_sleep_time)
        return nodeOutgoing

    def __init__(self, 
            modem:Modem, 
            daemon_sleep_time:int=3,
            prefetch_count:int=1,
            durable:bool=True,
            active_nodes:dict=None
            )->None:

        super().__init__()
        self.modem = modem
        self.durable = durable
        self.prefetch_count = prefetch_count
        self.daemon_sleep_time = daemon_sleep_time

        config_filepath = os.path.join(
                os.path.dirname(__file__), 
                '../../.configs', 'config.ini')

        # logging.debug("%s", config_filepath)
        config = configparser.ConfigParser()
        config.read(config_filepath)

        self.username=config['OUTGOING']['API_ID']
        self.queue_name = config['OUTGOING']['QUEUE_NAME']
        self.modem_operator = Deku.get_modem_operator_name(self.modem)

        logging.debug("%s", self.modem_operator)

        """
        format: queue_name

        (API_ID_QUEUE_NAME_OPERATOR_NAME)
        (username_QUEUE_NAME_OPERATOR_NAME)
        """
        self.queue_name=config['OUTGOING']['QUEUE_NAME'] + '_' + self.modem_operator

        """
        format: binding_key

        (API_ID_QUEUE_NAME.OPERATOR_NAME)
        (username_QUEUE_NAME.OPERATOR_NAME)
        """
        self.binding_key=config['OUTGOING']['QUEUE_NAME'] + '.' + self.modem_operator
        
        logging.debug("binding key: %s", self.binding_key)

        self.callback=self.__get_published__

        self.connection_url=config['OUTGOING']['CONNECTION_URL']
        self.password=config['OUTGOING']['API_KEY']

        self.exchange_name=config['OUTGOING']['EXCHANGE_NAME']
        self.exchange_type=config['OUTGOING']['EXCHANGE_TYPE']

    def __validate_repair_request__(self, number, method):
        try:
            Deku.validate_MSISDN(number)
        
        except Deku.InvalidNumber as error:
            logging.debug("invalid number, dumping message")
            self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

        except Deku.BadFormNumber as error:
            if error.message == 'MISSING_COUNTRY_CODE':
                logging.debug("Detected missing country code, attempting to repair...")

                try:
                    # TODO get country from modems
                    new_number = Deku.get_modem_country_code(self.modem) + number
                    Deku.validate_MSISDN(new_number)
                except Deku.InvalidNumber as error:
                    logging.error("invalid number, dumping message")
                    self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                    raise Exception("")

                except Deku.BadFormNumber as error:
                    logging.error("badly formed number, dumping message")
                    self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                    raise Exception("")
                
                except Exception as error:
                    logging.exception(error)
                    raise error

                else:
                    number = new_number
                    logging.debug("Repaired successful - %s", number)
            else:
                logging.error("invalid country code, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                raise Exception("")

        except Exception as error:
            logging.exception(error)
            raise error

        return number

    def __get_published__(self, ch, method, properties, body):
        try:
            json_body = json.loads(body.decode('utf-8'))
            if not "text" in json_body:
                logging.debug('text missing from request')
                return 
            
            if not "number" in json_body:
                logging.debug('number missing from request')
                return 

            text=json_body['text']
            number=json_body['number'].replace(' ', '')
        except Exception as error:
            return

        else:
            try:
                number=self.__validate_repair_request__(number, method)
            except Exception as error:
                self.outgoing_connection.sleep(self.daemon_sleep_time)
                return

            try:
                logging.debug("sending: [%s]%s %s", 
                        Deku.get_modem_operator_name(self.modem), 
                        self.modem.imei, body)

                deku = Deku(modem=self.modem)
                if deku.modem_ready():
                    deku.modem_send(
                            text=text,
                            number=number,
                            match_operator=True)
                else:
                    logging.debug("Modem not ready!")
                    raise Exception("modem not ready")

            except Deku.NoMatchOperator as error:
                ''' could either choose to republish to right operator or dump '''
                logging.error("no match operator, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

            except Deku.NoAvailableModem as error:
                logging.warning("no available modem while trying to send")
                self.outgoing_channel.basic_reject(
                        delivery_tag=method.delivery_tag, 
                        requeue=True)
                self.outgoing_connection.sleep(self.daemon_sleep_time)

            except subprocess.CalledProcessError as error:
                # logging.exception(error)
                self.outgoing_channel.basic_reject(
                        delivery_tag=method.delivery_tag, requeue=True)

            except Exception as error:
                self.outgoing_channel.basic_reject(
                        delivery_tag=method.delivery_tag, requeue=True)
                logging.exception(error)
            else:
                self.outgoing_channel.basic_ack(
                        delivery_tag=method.delivery_tag)
            """
            finally:
                if self.outgoing_channel.is_open:
                    return
            """

    def signal_thread(self):
        pass


    def main(self, connection_url:str='localhost',
            queue_name:str='outgoing.route.route')->None:

        """Monitors for incoming request and sends out SMS.

        This is process is blocking.

            Args:
                connection_url:
                    url of local rabbitmq broker.

                queue_name:
                    name of queue on rabbitmq where messages for routing
                    should routed to.
        """
        logging.debug("monitoring for incoming request")

        try:
            self.outgoing_connection, self.outgoing_channel = RabbitMQBroker.create_channel(
                    connection_url=self.connection_url,
                    queue_name=self.queue_name,
                    username=self.username,
                    password=self.password,
                    exchange_name=self.exchange_name,
                    exchange_type=self.exchange_type,
                    binding_key=self.binding_key,
                    callback=self.callback,
                    durable=self.durable,
                    prefetch_count=self.prefetch_count)
            logging.info("Connection established successfully")
        except Exception as error:
            logging.exception(error)
        else:
            try:
                # self.outgoing_channel.start_consuming() #blocking
                blocking_channel = threading.Thread(
                        target=self.outgoing_channel.start_consuming, daemon=True)
                blocking_channel.start()

                self.wait()
            except Exception as error:
                # raise error
                logging.exception(error)
            finally:
                if self.outgoing_connection.is_open:
                    self.outgoing_connection.close()
                    logging.debug("closed connection for %s", self.modem.imei)
