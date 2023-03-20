#!/usr/bin/env python3

import logging
import json

import pika

from DekuPython import Client
from DekuPython.std_carrier_lib.helpers import CarrierInformation

from modem_manager import ModemManager

from modem import Modem


class RMQModem:
    def __init__(self, modem: Modem, **kwargs) -> None:
        """ """
        self.ci_ = CarrierInformation()
        self.modem = modem
        self.configs = kwargs["configs"]

        self.connection_url = self.configs["DEKU"]["CONNECTION_URL"]
        self.connection_port = self.configs["DEKU"]["CONNECTION_PORT"]

        self.username = self.configs["DEKU"]["ACCOUNT_SID"]
        self.password = self.configs["DEKU"]["AUTH_TOKEN"]

        self.pid = self.configs["DEKU"]["PROJECT_ID"]
        self.service = self.configs["DEKU"]["SERVICE"]

        self.modem_operator_code = None
        self.queue_name = None
        self.binding_key = None
        self.modem_operator_name = None
        self.callback = None
        self.connection_name = None
        self.outgoing_connection = None
        self.outgoing_channel = None

    def rmq_close_connection(self) -> None:
        """ """
        try:
            logging.debug("closing rmq connection...")

            if hasattr(self, "outgoing_connection"):
                self.outgoing_connection.close()
        except Exception as error:
            logging.exception(error)

    def __rmq_connection__(self) -> None:
        """ """
        try:
            self.modem_operator_code = self.modem.get_3gpp_property("OperatorCode")
            self.modem_operator_name = self.ci_.get_operator_name(
                operator_code=self.modem_operator_code
            )

            service_name = Client.get_service_name_from_operator_code(
                pid=self.pid,
                service=self.service,
                operator_code=self.modem_operator_code,
            )

            self.queue_name = service_name
            self.binding_key = service_name

            self.callback = self.__rmq_incoming_request__

            self.connection_name = "sample_connection_name"

            if "FRIENDLY_NAME" in self.configs["DEKU"]:
                self.connection_name = (
                    self.configs["DEKU"]["FRIENDLY_NAME"]
                    + ":"
                    + self.modem_operator_name
                )

        except Exception as error:
            raise error

        else:
            logging.debug("creating rmq connection..")
            try:
                (
                    self.outgoing_connection,
                    self.outgoing_channel,
                ) = Client.create_channel(
                    vhost=self.username,
                    connection_url=self.connection_url,
                    connection_port=self.connection_port,
                    queue_name=self.queue_name,
                    username=self.username,
                    password=self.password,
                    exchange_name=self.pid,
                    binding_key=self.binding_key,
                    callback=self.callback,
                    connection_name=self.connection_name,
                )

            except pika.exceptions.AMQPConnectionError as error:
                raise error

            except Exception as error:
                raise error

    def rmq_connection(self) -> None:
        """ """
        import socket

        try:
            self.__rmq_connection__()

        except (socket.gaierror, pika.exceptions.AMQPConnectionError) as error:
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
        Afkanerd Deku sends back messages in JSON format.
        The messages come with 'text' and 'number' as keys.
        """

        try:
            json_body = json.loads(body.decode("utf-8"))
            logging.info("New sms request: %s", json_body)
            if not "text" in json_body:
                logging.error("text missing from request")
                return

            if not "number" in json_body:
                logging.error("number missing from request")
                return

        except Exception as error:
            return

        else:
            text = json_body["text"]
            number = json_body["number"].replace(" ", "")

            try:
                self.ci_.is_valid_number(MSISDN=number)

            except (self.ci_.NotE164Number, self.ci_.InvalidNumber) as error:
                logging.error(error)

                try:
                    ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as error:
                    logging.error(error)

            except Exception as error:
                logging.exception(error)

            else:
                if "MATCH_OPERATOR" in self.configs["DEKU"]:
                    """
                    # TODO verify that number matches operator of modem
                    # Cause human error
                    """
                    if int(self.configs["DEKU"]["MATCH_OPERATOR"]) == 1:

                        try:
                            MSISDN_oc = self.ci_.get_operator_code(MSISDN=number)

                            if not MSISDN_oc == self.modem_operator_code:

                                logging.error(
                                    "MATCH_OPERATOR set but failed to match MSISDN.\n"
                                    "Modem is [%s] but request is [%s] MSISDN",
                                    self.modem_operator_code,
                                    MSISDN_oc,
                                )
                                try:
                                    self.outgoing_channel.basic_reject(
                                        delivery_tag=method.delivery_tag, requeue=False
                                    )
                                except Exception as error:
                                    logging.error(error)

                                return

                        except Exception as error:
                            logging.exception(error)

                try:
                    """ """
                    # TODO:
                    logging.info("Sending new sms message...")

                    # TODO; this is blocking - careful

                    callback_url = (
                        None
                        if not "callback_url" in json_body
                        else json_body["callback_url"]
                    )

                    if callback_url:
                        callback_url = callback_url.split(",")

                    self.modem.messaging.send_sms(text=text, number=number)

                except Exception as error:
                    logging.exception(error)

                    try:
                        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                    except Exception as error:
                        logging.error(error)

                else:
                    # self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                    logging.info("sent sms successfully!")
                    try:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as error:
                        logging.error(error)


def modem_ready_handler(modem: Modem) -> None:
    """ """
    logging.debug("modem ready handler: %s", modem)

    """
    try:
        logging.debug("clearing stack for ready modem")
        modem.messaging.clear_stack()
    except Exception as error:
        logging.exception(error)
    """

    try:
        logging.debug("ready modem calling connection")
        rabbitmq_modem = RMQModem(modem=modem, configs=configs)

        modem.add_modem_is_not_ready_handler(rabbitmq_modem.rmq_close_connection)

        while modem.connected:
            logging.debug("[%s] starting rabbitmq connection...", modem.modem_path)
            try:
                rabbitmq_modem.rmq_connection()
            except Exception as error:
                logging.exception(error)

        logging.debug("ending rmq connection loop...")

    except Exception as error:
        logging.exception(error)


def modem_connected_handler(modem: Modem) -> None:
    """ """
    logging.debug("Modem connected outbound: %s", modem)

    if "AUTO_ENABLE" in configs["NODES"] and int(configs["NODES"]["AUTO_ENABLE"]) == 1:
        try:
            modem.enable()
            logging.info("Modem auto enabled...")
        except Exception as error:
            logging.exception(error)

    modem.add_modem_is_ready_handler(modem_ready_handler)
    modem.check_modem_is_ready()


def Main(modem_manager: ModemManager, *args, **kwargs) -> None:
    global configs

    configs = kwargs["configs"]
    modem_manager.add_modem_connected_handler(modem_connected_handler)
