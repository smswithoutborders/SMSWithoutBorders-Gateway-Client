#!/usr/bin/env python3

import os, sys
import logging
import configparser
import threading
import json
import time
import pika
import dbus

from modem_manager import ModemManager

from modem import Modem

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

    def __rmq_connection__(self) -> None:
        """
        """
        try:
            self.modem_operator_code = self.modem.get_3gpp_property("OperatorCode")
            self.modem_operator_name = helpers.get_operator_name(
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
                raise error

            except Exception as error:
                raise error


    def rmq_connection(self) -> None:
        """
        """
        try:
            self.__rmq_connection__()

        except pika.exceptions.AMQPConnectionError as error:
            logging.exception(error)

        except Exception as error:
            raise error
        
        else:
            try:
                logging.info("consumer for rmq started")
                self.outgoing_channel.start_consuming()

            except pika.exceptions.AMQPHeartbeatTimeout as error:
                logging.exception("heart beat failure issue")

            except Exception as error:
                logging.exception(error)

            finally:
                try:
                    self.outgoing_channel.close()
                    self.outgoing_connection.close()
                except Exception as error:
                    logging.error(error)

        logging.debug("End AMP connection for outbound...")


    def __rmq_incoming_request__(self, ch, method, properties, body) -> None:
        """
        SMSWithoutBorders OpenAPI sends back messages in JSON format.
        The messages come with 'text' and 'number' as keys.
        """

        try:
            json_body = json.loads(body.decode('utf-8'))
            logging.info("New sms request: %s", json_body)
            if not "text" in json_body:
                logging.error('text missing from request')
                return 
            
            if not "number" in json_body:
                logging.error('number missing from request')
                return 

        except Exception as error:
            return

        else:
            text=json_body['text']
            number=json_body['number'].replace(' ', '')

            try:
                helpers.is_valid_number(MSISDN=number)

            except (helpers.NotE164Number, helpers.InvalidNumber) as error:
                logging.error(error)
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
            except Exception as error:
                logging.exception(error)

            else:
                if 'MATCH_OPERATOR' in self.configs['OPENAPI']:
                    """
                    # TODO verify that number matches operator of modem
                    # Cause human error
                    """
                    if int(self.configs['OPENAPI']['MATCH_OPERATOR']) == 1:

                        try:
                            MSISDN_oc = helpers.get_operator_code(number)

                            if not MSISDN_oc == self.modem_operator_code:

                                logging.error("MATCH_OPERATOR set but failed to match MSISDN.\n"
                                "Modem is [%s] but request is [%s] MSISDN", 
                                        self.modem_operator_code, MSISDN_oc)
                                self.outgoing_channel.basic_reject(
                                        delivery_tag=method.delivery_tag, requeue=False)

                                return

                        except Exception as error:
                            logging.exception(error)

                try:
                    """
                    """
                    logging.info("Sending new sms message...")

                    # TODO; this is blocking - careful
                    self.modem.messaging.send_sms(
                            text=text,
                            number=number)

                except Exception as error:
                    logging.exception(error)
                    ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)

                else:
                    # self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logging.info("sent sms successfully!")


def modem_ready_handler(modem: Modem) -> None:
    """
    """
    try:
        logging.debug("clearing stack for ready modem")
        modem.messaging.clear_stack()
    except Exception as error:
        logging.exception(error)

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
