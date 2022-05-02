#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
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
from seeds import Seeds
from seeders import Seeders
from router import Router
import helpers

class NodeInbound(Seeds):
    locked_modems = True

    def __init__(self, 
            modem:Modem, 
            daemon_sleep_time:int=3, 
            configs__: configparser.ConfigParser=None)->None:

        # super().__init__()

        self.modem = modem
        self.daemon_sleep_time = daemon_sleep_time
        self.configs__ = configs__

        self.__seeder_timeout = configs__['NODES']['SEEDER_TIMEOUT']
        self.__seed_fail_timeout = configs__['NODES']['SEED_REQUEST_FAILED_TIMEOUT']

        # defaults __seeder_timeout to 160.0 seconds
        self.__seeder_timeout = float(self.__seeder_timeout) if self.__seeder_timeout != '' else 300.0

        Seeds.__init__(self, IMSI=modem.get_sim_imsi(), 
                seeder_timeout=self.__seeder_timeout)

    def __publish_to_broker__(self, sms:str, queue_name:str)->None:
        try:
            publish_data = {"text":sms.text, "MSISDN":sms.number}
            self.publish_channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(publish_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            logging.debug("published %s", publish_data)
        except Exception as error:
            raise error

    def process_seeder_response(self, sms: SMS, seeder: Seeders):
        logging.debug("+ Response made from seeder [%s]", seeder.MSISDN)

        if seeder.is_seeder_message(data = bytes(sms.text, 'utf-8')):
            logging.debug("MSISDN [%s] for this node", seeder.MSISDN)

            seed = Seeds(IMSI=self.modem.get_sim_imsi())
            seed_MSISDN = seed.process_seed_message(data=bytes(sms.text, 'utf-8'))

            logging.info("Updating seed record with: %s", seed_MSISDN)
            rowcount = seed.make_seed(MSISDN=seed_MSISDN)

            if rowcount < 1:
                logging.error("Failed to update seed record!")

            logging.debug("Updating seeder for node")
            seed.update_seeder(seeder_MSISDN=seeder.MSISDN)

            logging.info("[*] SEEDING COMPLETE!")
        else:
            logging.debug("Not a seeder message!")


    def process_seed_request(self, sms: SMS):
        """Responds back to seed with MSISDN.
        """
        logging.debug("+ Responding request made from seed [%s]", sms.number)
        text = str(base64.b64encode(bytes(json.dumps({"MSISDN": sms.number}), 'utf-8')), 'utf-8')
        try:
            logging.info("[*] Responding with SMS to seed request")
            Deku(self.modem).modem_send( 
                    number=sms.number,
                    text=text,
                    force=True)
        except Exception as error:
            raise error
        else:
            time.sleep(self.daemon_sleep_time)
            logging.info("[*] SEED RESPONSE COMPLETE")


    def listen_for_sms_inbound(self, 
            publish_url:str='localhost', 
            queue_name:str='inbound.route.route' )->None:
        """Checks for all incoming messages.
        Before processing the messages - checks if:
            - Is a seed request (critical to do this before messages get deleted).
            - Is a seeder response.
        """

        logging.info("[*] [%s | %s]: Starting incoming listener", 
                self.modem.imei, helpers.get_modem_operator_name(self.modem))

        while True:
            if(
                    not hasattr(self, 'publish_connection') or self.publish_connection.is_closed):

                logging.info("[*] Creating new connection for publishing")

                try:
                    self.publish_connection, self.publish_channel = \
                            RabbitMQBroker.create_channel(
                                connection_url=publish_url,
                                queue_name=queue_name,
                                heartbeat=600,
                                blocked_connection_timeout=60,
                                durable=True)
                except pika.exceptions.AMQPConnectionError as error:
                    logging.error(error)

                    """sleep and retry the connection"""
                    time.sleep(self.daemon_sleep_time)
                    continue
                
                except Exception as error:
                    logging.exception(error)
                    raise error

            inbound_messages = self.modem.sms.list('received')
            logging.debug("# of inbound messasges = %d", len(inbound_messages))

            for msg_index in inbound_messages:
                sms=Modem.SMS(index=msg_index)
                logging.debug("MSISDN:%s, Text:%s", 
                        sms.number, sms.text)

                try:
                    # data = {"MSISDN":sms.number, "IMSI":self.modem.get_sim_imsi(), "text":sms.text}

                    seeder = Seeders(MSISDN=sms.number)

                    # Seeder receiving request to make seed from IMSI
                    if Seeds.is_seed_message(data=bytes(sms.text, 'utf-8')):
                        logging.info("[*] Seeding request present")
                        self.process_seed_request(sms)

                    # Seed receiving response from seeder with MSISDN
                    elif seeder.is_seeder():
                        logging.info("[*] Seeder response present")
                        self.process_seeder_response(sms=sms, seeder=seeder)

                except Exception as error:
                    logging.exception(error)
                
                try:
                    self.__publish_to_broker__(sms=sms, queue_name=queue_name)
                except Exception as error:
                    # self.logging.critical(error)
                    raise error

                else:
                    try:
                        self.modem.sms.delete(msg_index)
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
            # inbound_messages=[]
            time.sleep(self.daemon_sleep_time)


    def make_seeder_request(self, seeder: Seeders) -> None:
        """Sends a request to the provided seeder.
        """
        text = json.dumps({"IMSI": self.modem.get_sim_imsi()})

        text = str(base64.b64encode(str.encode(text)), 'utf-8')

        """Checks if state requested has expired, then goes ahead to make request if yes"""

        logging.info("[*] Making request to seeder: %s %s", 
                seeder.MSISDN, text)
        try:
            Deku(self.modem).modem_send( 
                    number=seeder.MSISDN,
                    text=text,
                    force=True)
        except Exception as error:
            """Sleep before sending this because it stops the entire daemon"""
            time.sleep(self.__seed_fail_timeout)
            raise error
        else:
            try:
                self.update_state(seeder_MSISDN=seeder.MSISDN, state='requested')
                logging.debug("Seeder %s state changed to requested", seeder.MSISDN)
                time.sleep(self.daemon_sleep_time)

            except Seeds.InvalidSeedState as error:
                raise error

            except Exception as error:
                raise error


    def __seed__(self) -> None:
        # raise Exception("--> raising this for testing purposes")
        seeders = []
        remote_gateway_servers = self.configs__['NODES']['SEEDERS_PROBE_URLS']

        """Ask remote server for seeders"""
        remote_gateway_servers = [s.strip() for s in remote_gateway_servers.split(',')]
        logging.debug("Remote Gateways servers: %s", remote_gateway_servers)

        try:
            seeders = Seeders.request_remote_seeders(remote_gateway_servers)

        except Exception as error:
            logging.exception(error)

        else:
            if len(seeders) > 0:
                logging.info("[*] Available seeders: %s", [seeder for seeder in seeders])
            else:
                logging.debug("No remote seeders found, checking for hardcoded")


        if len(seeders) < 1:
            """Important: Should never be empty"""
            logging.info("[*] Falling back to hardcoded seeders")
            seeders = Seeders.request_hardcoded_seeders()

        logging.debug("Acquired seeders: %s", [seeder.MSISDN for seeder in seeders])

        filtered_seeders = []
        """
        filtered_seeders = Seeders._filter(seeders, 
                {"country":helpers.get_modem_operator_country(self.modem),
                    "operator_name":helpers.get_modem_operator_name(self.modem)})

        if not filtered_seeders:
            logging.debug("No seeders found for filter, trying with lesser filters")
            filtered_seeders = Seeders._filter(seeders, 
                    {"country":helpers.get_modem_operator_country(self.modem)})
        else:
            logging.debug("%d filtered seeders found!", len(filtered_seeders))
        """

        if len(filtered_seeders) > 0:
            logging.debug("%d filtered seeders found!", len(filtered_seeders))
            seeder = filtered_seeders[0]
        else:
            logging.debug("no seeders found, falling back to unfiltered ones")
            seeder = seeders[0]

        try:
            logging.debug("making seeder request [%s]", seeder.MSISDN)
            self.make_seeder_request(seeder=seeder)
        except Exception as error:
            raise error
        else:
            logging.info("Seed request made successfully!")

    def daemon_seed_checker(self) -> None:
        """
        """
        try:
            logging.info("[*] [%s | %s]: Starting daemon seed checker", 
                    self.modem.imei, helpers.get_modem_operator_name(self.modem))

            IMSI= self.modem.get_sim_imsi()

            #  Checcks of current node is a seed (has MSISDN and IMSI in ledger)
            if not self.is_seed():
                logging.info("[*] Node is not a seed!")

                try:
                    if not self.can_request_MSISDN():
                        logging.info("[*] MSISDN request still pending expiring... waiting")
                        return

                except Exception as error:
                    logging.exception(error)
                else:
                    remote_gateway_servers = self.configs__['NODES']['SEEDS_PROBE_URLS']
                    remote_gateway_servers = [s.strip() for s in remote_gateway_servers.split(',')]
                    MSISDN = self.remote_search(remote_gateway_servers)

                    if MSISDN == '':
                        logging.debug("[%s] is not a seed... fetching remote seeders", self.IMSI)
                        self.__seed__()
                    else:
                        logging.debug("Updating seed record with: %s", MSISDN)
                        rowcount = self.make_seed(MSISDN=MSISDN)

                        if rowcount < 1:
                            logging.error("Failed to update seed record!")
                        else:
                            logging.debug("[*] MSISDN - %s found remotely!", MSISDN)
            else:
                logging.info("Node is valid seed!")

        except Exception as error:
            # logging.error(error)
            logging.exception(error)


    def listen_for_routing_request(self, 
            callback_function,
            publisher_connection_url: str = 'localhost',
            queue_name: str='inbound.route.route',
            route_url: str = 'localhost') -> None:
        """
        """
        logging.info("[*] [%s | %s]: Starting routing request listener", 
                self.modem.imei, helpers.get_modem_operator_name(self.modem))

        try:
            self.router_connection, self.router_channel = RabbitMQBroker.create_channel( 
                    connection_url=publisher_connection_url,
                    callback=callback_function,
                    queue_name=queue_name)

            routing_request_thread = threading.Thread(
                    target=self.router_channel.start_consuming, daemon=True)

            routing_request_thread.start()

        except pika.exceptions.ConnectionClosedByBroker as error:
            logging.exception(error)


    def router_callback(self, ch, method, properties, body: bytes) -> None:
        """
        """
        try:
            decoded_body = body.decode('unicode_escape')
            json_body = json.loads(decoded_body, strict=False)

        except Exception as error:
            """This most likely is not a request -> cus how did it get here if not JSON?"""
            logging.exception(error)

        else:
            if not "text" in json_body:
                """This most likely is not a request -> cus how did it get here if not contain text?"""
                logging.error('poorly formed message - text missing')
                # self.router_channel.basic_ack(delivery_tag=method.delivery_tag)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            if not "MSISDN" in json_body:
                """This most likely is not a request -> cus how did it get here if not contain phone number?"""
                logging.error('poorly formed message - number missing')
                # self.router_channel.basic_ack(delivery_tag=method.delivery_tag)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            try:
                """Routing online"""
                routing_urls = self.configs__['NODES']['ROUTING_URLS']
                routing_urls = [url.strip() for url in routing_urls.split(',')]

                for routing_url in routing_urls:
                    logging.info("[*] Routing %s -> %s", json_body, routing_url)

                    router = Router(url=routing_url)
                    router.route_online(data=json_body)
            except Exception as error:
                logging.exception(error)
                # self.router_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
                ch.basic_reject( delivery_tag=method.delivery_tag)
            else:
                # self.router_channel.basic_ack( delivery_tag=method.delivery_tag)
                ch.basic_ack( delivery_tag=method.delivery_tag)
            finally:
                time.sleep(self.daemon_sleep_time)


    def main(self) -> None:
        """Monitors modems for inbound messages and publishes.
        This is process is blocking.
        All seed(er)s make a ping request to the servers to inform of their presence

        TODO:
            - Ping body (IMSI: str, MSISDN: str, seeder: bool)
        """

        logging.info("[*] [BEGAN MAIN FOR MODULE FOR NODE INCOMING]")
        try:
            daemon_seed_checker_thread = threading.Thread(target=self.daemon_seed_checker,
                    daemon=True)
            daemon_seed_checker_thread.start()
        except Exception as error:
            logging.exception(error)
            time.sleep(self.daemon_sleep_time)


        try:
            ping_servers = self.configs__['NODES']['SEED_PING_URLS']
            ping_servers = [server.strip() for server in ping_servers.split(',')]
            self.start_pinging(ping_servers = ping_servers, ping_duration=10.0)
        except Exception as error:
            logging.exception(error)


        try:
            inbound_thread = threading.Thread(
                    target=self.listen_for_sms_inbound, 
                    daemon=True)
            inbound_thread.start()
        except Exception as error:
            logging.exception(error)


        try:
            routing_thread = threading.Thread(
                    target=self.listen_for_routing_request, 
                    args=(self.router_callback,),
                    daemon=True)
            routing_thread.start()
        except Exception as error:
            logging.exception(error)


        try:
            self.wait()
            self.stop_ping()
        except Exception as error:
            logging.exception(error)

        logging.info("[*] [STOPPED MAIN FOR MODULE FOR NODE INCOMING]")

