#!/usr/bin/env python3

from __future__ import annotations

import logging 
from common.mmcli_python.modem import Modem

class NodeIncoming:
    def __init__(cls, modem:Modem, daemon_sleep_time:int=3)->None:
        self.modem = modem
        self.daemon_sleep_time = daemon_sleep_time

    @classmethod
    def init(cls, modem:Modem, daemon_sleep_time:int=3)->NodeIncoming:
        nodeIncoming = NodeIncoming(modem, daemon_sleep_time)
        return nodeIncoming

    def __publish_to_broker__(self, sms, queue_name):
        try:
            publish_data = {"text":sms.text, "number":sms.number}
            self.publish_channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(publish_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            self.logging.info("published %s", publish_data)
        except Exception as error:
            raise error

    def main(self, publish_url:str='localhost', 
            queue_name:str='incoming.route.route') -> None:
        logging.debug("NodeIncoming main called...")
        """Monitors modems for incoming messages and publishes.
        """

        """
        try:
            while Deku.modem_ready(self.modem, index_only=True):
                if not hasattr(self, 'publish_connection') or \
                        self.publish_connection.is_closed:

                    self.publish_connection, self.publish_channel = create_channel(
                            connection_url=connection_url,
                            queue_name=queue_name,
                            heartbeat=600,
                            blocked_connection_timeout=60,
                            durable=True)

                incoming_messages = self.modem.SMS.list('received')
                for msg_index in incoming_messages:
                    sms=Modem.SMS(index=msg_index)

                    try:
                        self.__publish_to_broker__(sms=sms, queue_name=queue_name)
                    except Exception as error:
                        self.logging.critical(error)

                    else:
                        try:
                            self.modem.SMS.delete(msg_index)
                        except Exception as error:
                            self.logging.error(traceback.format_exc())
                        else:
                            try:
                                self.__exec_remote_control__(sms)
                            except Exception as error:
                                self.logging.exception(traceback.format_exc())

                incoming_messages=[]
                time.sleep(self.sleep_time)

        except Modem.MissingModem as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem.index)
        except Modem.MissingIndex as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
            self.logging.warning("Modem [%s] Index not initialized", self.modem.index)
        except Exception as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem.index)
            self.logging.critical(traceback.format_exc())
        finally:
            time.sleep(self.sleep_time)

        try:
            if self.modem.index in active_threads:
                del active_threads[self.modem.index]
        except Exception as error:
            raise error
        """

    def __del__(self):
        if self.publish_connection.is_open:
            self.publish_connection.close()
        self.logging.debug("cleaned up gateway instance")
