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
from rabbitmq_broker import RabbitMQBroker
from router import Router
import helpers

class RMQModem:

    def __init__(self, modem: Modem, **kwargs) -> None:
        """
        """
        self.modem = modem
        self.configs = kwargs['configs']

        self.connection_url=self.configs['OPENAPI']['CONNECTION_URL']
        self.connection_port=self.configs['OPENAPI']['CONNECTION_PORT']

        self.username=self.configs['OPENAPI']['API_ID']
        self.password=self.configs['OPENAPI']['API_KEY']


        self.exchange_name=self.configs['OPENAPI']['EXCHANGE_NAME']
        self.exchange_type=self.configs['OPENAPI']['EXCHANGE_TYPE']

        logging.debug("exchange name: %s", self.exchange_name)
        logging.debug("exchange type: %s", self.exchange_type)


    def rmq_close_connection(self) -> None:
        """
        """
        try:
            logging.debug("closing rmq connection...")

            if hasattr(self, "outgoing_connection"):
                self.outgoing_connection.close()
        except Exception as error:
            logging.exception(error)



    def rmq_connection(self) -> None:
        """
        """
        try:
            self.modem_operator_code = self.modem.get_3gpp_property("OperatorCode")
            self.modem_operator_name = helpers.get_modem_operator_name(
                    operator_code=self.modem_operator_code)

            logging.debug("modem operator code: %s", self.modem_operator_code)
            logging.debug("modem operator name: %s", self.modem_operator_name)

            """
            + format for queue_name----
            (API_ID_QUEUE_NAME_OPERATOR_NAME)
            (username_QUEUE_NAME_OPERATOR_NAME)

            + format for binding_key----
            (API_ID_QUEUE_NAME.OPERATOR_NAME)
            (username_QUEUE_NAME.OPERATOR_NAME)
            """

            queue_name = self.configs['OPENAPI']['QUEUE_NAME']

            self.queue_name = queue_name + '_' + self.modem_operator_name
            self.binding_key = queue_name + '.' + self.modem_operator_name

            logging.debug("queue name: %s", self.queue_name)
            logging.debug("binding key: %s", self.binding_key)

            self.callback=self.__rmq_incoming_request__

            self.connection_name = "sample_connection_name"

            if 'FRIENDLY_NAME' in self.configs['OPENAPI']:
                self.connection_name = \
                        self.configs['OPENAPI']['FRIENDLY_NAME'] + ":" \
                        + self.modem_operator_name


        except Exception as error:
            raise error

        else:
            logging.debug("creating rmq connection..")
            try:
                self.outgoing_connection, self.outgoing_channel = RabbitMQBroker.create_channel(
                        connection_url=self.connection_url,
                        connection_port=self.connection_port,
                        queue_name=self.queue_name,
                        username=self.username,
                        password=self.password,
                        exchange_name=self.exchange_name,
                        exchange_type=self.exchange_type,
                        binding_key=self.binding_key,
                        callback=self.callback,
                        connection_name=self.connection_name)

            except pika.exceptions.AMQPConnectionError as error:
                logging.exception(error)

            except Exception as error:
                logging.exception(error)

            else:
                try:
                    logging.info("consumer for rmq started")
                    self.outgoing_channel.start_consuming()

                except pika.exceptions.AMQPHeartbeatTimeout as error:
                    logging.exception("heart beat failure issue")

                finally:
                    try:
                        self.outgoing_channel.close()
                        self.outgoing_channel.close()
                    except Exception as error:
                        logging.error(error)

            logging.debug("End AMP connection for outbound...")


    def __rmq_incoming_request__(self, ch, method, properties, body) -> None:
        """
        """

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

            """
            try:
                logging.debug("sending: [%s]%s %s", 
                        helpers.get_modem_operator_name(self.modem), 
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

            except helpers.InvalidNumber as error:
                logging.debug("invalid number, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

            except helpers.InvalidNumber as error:
                logging.error("invalid number, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

            except helpers.BadFormNumber as error:
                logging.error("badly formed number, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)


            except helpers.NoMatchOperator as error:
                ''' could either choose to republish to right operator or dump '''
                logging.error("no match operator, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

            except helpers.NoAvailableModem as error:
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
                self.outgoing_connection.sleep(self.daemon_sleep_time)
                logging.exception(error)

                if error.args[0] == helpers.INVALID_COUNTRY_CODE_EXCEPTION:
                    logging.warning("[-] MESSAGE SHALL NOT PASS!!")

                else:
                    self.outgoing_channel.basic_reject(
                            delivery_tag=method.delivery_tag, requeue=True)
            
            else:
                self.outgoing_channel.basic_ack(
                        delivery_tag=method.delivery_tag)
            finally:
                if self.outgoing_channel.is_open:
                    return
            """


def modem_ready_handler(modem: Modem) -> None:
    """
    """
    try:
        logging.debug("ready modem calling connection")
        rabbitmq_modem = RMQModem(modem=modem, configs=configs)

        modem.add_modem_is_not_ready_handler(rabbitmq_modem.rmq_close_connection)

        while modem.connected and modem.is_ready():
            logging.debug("[%s] starting rabbitmq connection...", modem.modem_path)
            rabbitmq_modem.rmq_connection()

        logging.debug("ending rmq connection loop...")

    except Exception as error:
        logging.exception(error)


def modem_connected_handler(modem: Modem) -> None:
    """
    """
    modem.add_modem_is_ready_handler(modem_ready_handler)
    modem.check_modem_is_ready()


def main(modem_manager: ModemManager, *args, **kwargs)->None:
    global configs

    configs = kwargs['configs']
    modem_manager.add_modem_connected_handler(modem_connected_handler)
