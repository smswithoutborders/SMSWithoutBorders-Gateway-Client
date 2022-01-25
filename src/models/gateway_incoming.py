#!/usr/bin/env python3

from __future__ import annotations

import logging 
import pika
import time
import json

from common.mmcli_python.modem import Modem
from deku import Deku
from rabbitmq_broker import RabbitMQBroker

class NodeIncoming:
    def __init__(self, modem:Modem, 
            daemon_sleep_time:int=3, 
            active_nodes:dict=None)->None:
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
