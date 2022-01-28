#!/usr/bin/env python3

from __future__ import annotations

import logging 
import pika
import time
import json
import threading

from common.mmcli_python.modem import Modem
from deku import Deku
from rabbitmq_broker import RabbitMQBroker
from ledger import Ledger

class NodeIncoming(threading.Event):
    def __init__(self, modem:Modem, 
            daemon_sleep_time:int=3, 
            active_nodes:dict=None)->None:

        super().__init__()
        self.modem = modem
        self.daemon_sleep_time = daemon_sleep_time
        self.active_nodes = active_nodes

    @classmethod
    def init(cls, modem:Modem, daemon_sleep_time:int=3, 
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


    def __is_seeder__(self, MSISDN:str) -> list:
        """Returns a list of Seeder Gateway addresses.
        TODO:
            Thinking of making sure each seeder Gateway get's some unique values to it
                even if their communicating MSISDN changes

            {"MSISDN": ["route urls",..]}
        """

        seeders = []
        ledger = Ledger('seeders')

        try:
            return ledger.exist(data={"MSISDN":MSISIDN})
        except Exception as error:
            raise error


    def is_ledger_request(self, data:dict) -> bool:
        """Validates incoming SMS is a valid ledger response.

        Checks the data for the following:
            1. Number:
                Checks if number is a valid Gateway Seeder number - seeder list
            2. Text:
                Checks the body of the text if:
                    1. Is base64 encoded.
                    2. Is JSON.
                    3. Contains MSISDN.
                    4. Is valid MSISDN.
                    5. MSISIDN country matches country of SIM Operator CODE (MCCMNC).
        This creates the ledger record and number acquisition is complete.
        """

        try:
            if not self.__is_seeder__(data['MSISDN']):
                return False

            try:
                # 1. 
                text = base64.b64decode(data['text'])
            except Exception as error:
                logging.exception(error)
                logging.debug("Not a valid base64 number")
                raise error

            else:
                try:
                    # 2.
                    text = json.loads(text)
                except Exception as error:
                    logging.exception(error)
                    logging.debug("Not a valid json object")
                    raise error

                else:
                    # 3.
                    if not 'MSISDN' in text:
                        logging.debug("does not contain MSISDN")
                        return False
                    else:
                        # 4.
                        try:
                            MSISDN_country, _ = Deku.validate_MSISDN(MSISDN=text['MSISDN'])
                        except Deku.InvalidNumber as error:
                            logging.debug("Is not a valid MSISDN")
                            raise error

                        except Deku.BadFormNumber as error:
                            """
                            TODO: 
                                This error comes with 2 types (src/deku.py)
                            """
                            raise error

                        except Exception as error:
                            raise error

                        else:
                            # 5.
                            MCCMNC_country = Deku.get_modem_operator_country(self.modem)

                            if not MSISDN_country == MCCMNC_country:
                                logging.debug("MSISDN country does not match MCCMNC country")
                                return False

                            else:
                                logging.info("Valid ledger request: %s", data)
                                return True

        except Exception as error:
            raise error

        return False



    def main(self, publish_url:str='localhost', 
            queue_name:str='incoming.route.route') -> None:

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

        """
        TODO: 
            Check if modem (simcard) has records stored -
            if not - make request
        """

        try:
            ledger = Ledger(populate=False)

        except Exception as error:
            raise error
        else:
            try:
                data = {"IMSI":self.modem.operator_code}
                if not ledger.exist(data=data, table='clients'):
                    logging.debug("No record found for this Gateway, making request")
                    """
                    TODO:
                        Make request for SMS message here
                    """
                    # Deku.send(force=True)
                else:
                    logging.debug("Record exist in ledger")
            except Exception as error:
                raise error

            try:
                while Deku.modem_ready(self.modem, index_only=True):
                    if not hasattr(self, 'publish_connection') or \
                            self.publish_connection.is_closed:

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
                            data = {"MSISDN":sms.number, "IMSI":self.modem.imsi, "text":sms.text}
                            """
                            Checks if record exist in ledger (ledger already exist)
                            If not exist, check if incoming is for ledger
                            If for ledger insert record in ledger and continue (Number has been acquired)
                            """
                            logging.debug("checking if data is ledger")

                            ledger = Ledger(['clients'])

                            if not ledger.exist(data=data):
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

            except Modem.MissingModem as error:
                logging.exception(error)

            except Modem.MissingIndex as error:
                logging.exception(error)

            except Exception as error:
                logging.exception(error)

            finally:
                time.sleep(self.daemon_sleep_time)

    def __del__(self):
        logging.debug("cleaned up node_incoming instance")
