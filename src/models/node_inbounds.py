#!/usr/bin/env python3

from __future__ import annotations

import os
import configparser
import logging 
import pika
import time
import json
import threading
import base64

from common.mmcli_python.modem import Modem
from deku import Deku
from rabbitmq_broker import RabbitMQBroker
from ledger import Ledger

class NodeIncoming(threading.Event):
    locked_modems = True

    def __init__(self, modem:Modem, 
            daemon_sleep_time:int=3, 
            active_nodes:dict=None)->None:

        super().__init__()
        self.modem = modem
        self.daemon_sleep_time = daemon_sleep_time
        self.active_nodes = active_nodes

    @staticmethod
    def init(modem:Modem, daemon_sleep_time:int=3, 
            active_nodes:dict=None)->NodeOutgoing:
        """Create an instance of :cls:NodeOutgoing.

            Args:
                modem: Instanstiates a node for this modem.
                daemon_sleep_time: Sleep time for each modem.
                active_nodes: from :cls:ModemManager to manage active nodes.
        """
        nodeIncoming = NodeIncoming(modem, daemon_sleep_time, active_nodes)
        return nodeIncoming

    def __publish_to_broker__(self, sms:str, queue_name:str)->None:
        try:
            publish_data = {"text":sms.text, "number":sms.number}
            self.publish_channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(publish_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            logging.debug("published %s", publish_data)
        except Exception as error:
            raise error


    def listen_for_sms_incoming(self, publish_url:str='localhost', queue_name:str='incoming.route.route' )->None:
        while True:
            if ( not hasattr(self, 'publish_connection') or 
                    self.publish_connection.is_closed):

                logging.debug("creating new connection for publishing")

                self.publish_connection, self.publish_channel = \
                        RabbitMQBroker.create_channel(
                            connection_url=publish_url,
                            queue_name=queue_name,
                            heartbeat=600,
                            blocked_connection_timeout=60,
                            durable=True)

            incoming_messages = self.modem.SMS.list('received')
            for msg_index in incoming_messages:
                sms=Modem.SMS(index=msg_index)
                logging.debug("Number:%s, Text:%s", 
                        sms.number, sms.text)

                try:
                    data = {"MSISDN":sms.number, "IMSI":self.modem.get_sim_imsi(), "text":sms.text}
                    """
                    Checks if record exist in ledger (ledger already exist)
                    If not exist, check if incoming is for ledger
                    If for ledger insert record in ledger and continue (Number has been acquired)
                    """
                    logging.debug("checking if data is ledger")

                    ledger = Ledger(['clients'])

                    if not ledger.client_record_exist(data=data):
                        if self.is_ledger_request(data):
                            ledger.insert_client_record(data)
                            logging.debug("Created new ledger")
                        else:
                            logging.debug("Not a ledger command")
                    else:
                        logging.debug("record exist, continuing to publish")
                except Exception as error:
                    logging.exception(error)
                
                try:
                    self.__publish_to_broker__(sms=sms, queue_name=queue_name)
                except Exception as error:
                    # self.logging.critical(error)
                    raise error

                else:
                    try:
                        self.modem.SMS.delete(msg_index)
                    except Exception as error:
                        raise error
                    '''
                    else:
                        try:
                            self.__exec_remote_control__(sms)
                        except Exception as error:
                            # self.logging.exception(traceback.format_exc())
                            raise error
                    '''
            # incoming_messages=[]
            time.sleep(self.daemon_sleep_time)


    def main(self) -> None:

        """Monitors modems for incoming messages and publishes.

        This is process is blocking.

            Args:
                publish_url:
                    url of local rabbitmq broker.

                queue_name:
                    name of queue on rabbitmq where messages for routing
                    should routed to.
        """

        logging.debug("monitoring incoming messages")

        try:
            self.validate_has_MSISDN()
            # return

        except Exception as error:
            raise error

        else:
            try:
                incoming_thread = threading.Thread(
                        target=self.listen_for_sms_incoming, 
                        daemon=True)
                incoming_thread.start()
                self.wait()
                logging.debug("stopping incoming listener")

            except Modem.MissingModem as error:
                logging.exception(error)

            except Modem.MissingIndex as error:
                logging.exception(error)

            except Exception as error:
                logging.exception(error)

            finally:
                time.sleep(self.daemon_sleep_time)
