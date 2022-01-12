#!/usr/bin/env python3

import time 
import os
import pika
import socket
import threading
import traceback
import json
import requests
import logging
from datetime import datetime
from base64 import b64encode

from deku import Deku
from enum import Enum

from common.mmcli_python.modem import Modem
from common.CustomConfigParser.customconfigparser import CustomConfigParser
from router import Router
from remote_control import RemoteControl

class Gateway:

    def __init__(self, modem_index, modem_isp, config, 
            config_isp_default, config_isp_operators, ssl=None):

        self.modem_index = modem_index
        self.modem_isp = modem_isp
        self.config = config

        formatter = logging.Formatter(
                '%(asctime)s|[%(levelname)s][%(module)s] [%(name)s] %(message)s', 
                datefmt='%Y-%m-%d %H:%M:%S')

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger_name=f"{self.modem_isp}:{self.modem_index}"
        self.logging=logging.getLogger(logger_name)
        self.logging.setLevel(logging.NOTSET)
        self.logging.addHandler(handler)

        '''
        log_file_path = os.path.join(os.path.dirname(__file__), 'services/logs', 'service.log')
        handler = logging.FileHandler(log_file_path)
        '''
        handler.setFormatter(formatter)
        self.logging.addHandler(handler)

        self.logging.propagate = True
        self.sleep_time = int(self.config['MODEMS']['sleep_time'])

    def __publish__(self, sms, queue_name):
        try:
            self.publish_channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps({"text":sms.text, "phonenumber":sms.number}),
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            self.logging.info("published %s",{"text":sms.text, "phonenumber":sms.number})
        except Exception as error:
            raise error

    def __exec_remote_control__(self, sms):
        try:
            self.logging.debug("Checking for remote control [%s] - [%s]", 
                    sms.text, sms.number)
            if RemoteControl.is_executable(text=sms.text):
                self.logging.info("Valid remote control activated [%s]", 
                        sms.text)
                if RemoteControl.is_whitelist(number=sms.number):
                    output = RemoteControl.execute(text=sms.text)
                    self.logging.debug(output)
                else:
                    self.logging.warning(
                            "Remote Control requester not whitelisted - [%s]",
                            sms.number)
            else:
                self.logging.debug("Not valid remote control command")
        except Exception as error:
            raise error


    def monitor_incoming(self):
        connection_url=self.config['GATEWAY']['connection_url']
        queue_name=self.config['GATEWAY']['routing_queue_name']

        # self.logging.info("incoming %s", self.modem_index)
        try:
            while Deku.modem_ready(self.modem_index, index_only=True):
                if not hasattr(self, 'publish_connection') or \
                        self.publish_connection.is_closed:
                    self.publish_connection, self.publish_channel = create_channel(
                            connection_url=connection_url,
                            queue_name=queue_name,
                            heartbeat=600,
                            blocked_connection_timeout=60,
                            durable=True)

                messages=Modem(self.modem_index).SMS.list('received')
                # self.logging.debug(messages)
                for msg_index in messages:
                    sms=Modem.SMS(index=msg_index)

                    try:
                        self.__publish__(sms=sms, queue_name=queue_name)
                    except Exception as error:
                        self.logging.critical(error)

                    else:
                        try:
                            Modem(self.modem_index).SMS.delete(msg_index)
                        except Exception as error:
                            self.logging.error(traceback.format_exc())
                        else:
                            try:
                                self.__exec_remote_control__(sms)
                            except Exception as error:
                                self.logging.exception(traceback.format_exc())

                messages=[]
                time.sleep(self.sleep_time)

        except Modem.MissingModem as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
        except Modem.MissingIndex as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
            self.logging.warning("Modem [%s] Index not initialized", self.modem_index)
        except Exception as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
            self.logging.critical(traceback.format_exc())
        finally:
            # self.logging.info(">> sleep time %s", self.sleep_time)
            time.sleep(self.sleep_time)

        # self.logging.warning("disconnected") 
        try:
            if self.modem_index in active_threads:
                del active_threads[self.modem_index]
        except Exception as error:
            raise error

    def __del__(self):
        if self.publish_connection.is_open:
            self.publish_connection.close()
        self.logging.debug("cleaned up gateway instance")



def init_nodes(indexes, config, config_isp_default, config_isp_operators, config_event_rules):
    isp_country = config['ISP']['country']

    deku=Deku(config=config, 
            config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    for modem_index in indexes:
        if modem_index not in active_threads:
            if not deku.modem_ready(modem_index, index_only=True):
                continue
            try:
                modem_isp = deku.ISP.modems(
                        operator_code=Modem(modem_index).operator_code, 
                        country=isp_country)

                gateway=Gateway(modem_index, modem_isp, config, 
                        config_isp_default, config_isp_operators)

                gateway_thread=threading.Thread(
                        target=gateway.monitor_incoming, daemon=True)

                active_threads[modem_index] = [gateway_thread, gateway]

            except Exception as error:
                raise error

def start_nodes():
    for modem_index, thread_n_node in active_threads.items():
        thread = thread_n_node[0]
        try:
            if thread.native_id is None:
                logging.info("starting thread for %s", modem_index)
                thread.start()

        except Exception as error:
            raise error

def manage_modems(config, config_event_rules, config_isp_default, config_isp_operators):
    global active_threads
    global sleep_time

    sleep_time = int(config['MODEMS']['sleep_time']) if \
            int(config['MODEMS']['sleep_time']) > 3 else 3

    active_threads = {}

    logging.info('modem manager started')
    while True:
        logging.debug("routing thread alive %s", routing_thread)
        indexes=[]
        try:
            indexes, locked_indexes = deku.modems_ready(remove_lock=True, index_only=True)
            stdout_logging.info("available modems %d %s, locked modems %d %s", 
                    len(indexes), indexes, len(locked_indexes), locked_indexes)

            if len(indexes) < 1:
                time.sleep(sleep_time)
                continue

        except Exception as error:
            raise error
        
        try:
            init_nodes(indexes, config, config_isp_default, 
                    config_isp_operators, config_event_rules)
            start_nodes()
        except Exception as error:
            raise error
        time.sleep(sleep_time)


def route_online(data):
    try:
        results = router.route_online(data=data)
        logging.info("routing results (online) %s %d", 
                results.text, results.status_code)
    except Exception as error:
        raise error

def route_offline(text, number):
    try:
        results = router.route_offline(text=text, number=number)
        logging.info("routing results (offline) successful")
    except Exception as error:
        raise error

def sms_routing_callback(ch, method, properties, body):
    logging.debug(body)
    json_body = json.loads(body.decode('unicode_escape'), strict=False)
    logging.info("routing %s", json_body)

    if not "text" in json_body:
        logging.error('poorly formed message - text missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    if not "phonenumber" in json_body:
        logging.error('poorly formed message - number missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        json_data = json.dumps(json_body)
        body = str(b64encode(body), 'unicode_escape')

        logging.debug("routing mode %s", router_mode)
        if router_mode == Router.Modes.ONLINE.value:
            route_online(json_data)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif router_mode == Router.Modes.OFFLINE.value:
            route_offline(body, router_phonenumber)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif router_mode == Router.Modes.SWITCH.value:
            try:
                route_online(json_data)
                routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as error:
                try:
                    route_offline(body, router_phonenumber)
                    routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as error:
                    raise error
        else:
            logging.error("invalid routing protocol")
    except Exception as error:
        logging.exception(traceback.format_exc())
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
    finally:
        routing_consume_connection.sleep(sleep_time)

def create_channel(connection_url, queue_name, exchange_name=None, 
        exchange_type=None, durable=False, binding_key=None, callback=None, 
        prefetch_count=0, connection_port=5672, heartbeat=600, 
        blocked_connection_timeout=None, username='guest', password='guest', retry_delay=10):

    credentials=pika.PlainCredentials(username, password)
    try:
        parameters=pika.ConnectionParameters(
                connection_url, 
                connection_port, 
                '/',
                credentials,
                retry_delay=retry_delay)

        connection=pika.BlockingConnection(parameters=parameters)
        channel=connection.channel()
        channel.queue_declare(queue_name, durable=durable)
        channel.basic_qos(prefetch_count=prefetch_count)

        if binding_key is not None:
            channel.queue_bind(
                    exchange=exchange_name,
                    queue=queue_name,
                    routing_key=binding_key)

        if callback is not None:
            channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=callback)

        return connection, channel
    except Exception as error:
        raise error


def rabbitmq_connection(config):
    connection_url=config['GATEWAY']['connection_url']
    queue_name=config['GATEWAY']['routing_queue_name']

    logging.info("attempting connection for %s (%s)", connection_url, queue_name)
    try:
        routing_consume_connection, routing_consume_channel = create_channel(
                connection_url=connection_url,
                callback=sms_routing_callback,
                durable=True,
                prefetch_count=1,
                queue_name=queue_name)

        # logging.info("connected to localhost")
        return routing_consume_connection, routing_consume_channel

    except Exception as error:
        raise error

def main(config, config_event_rules, config_isp_default, config_isp_operators):
    global router_mode
    global router_phonenumber
    global router
    global stdout_logging
    global deku

    formatter = logging.Formatter('%(asctime)s|[%(levelname)s] [%(filename)s] %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    stdout_logging=logging.getLogger('stdout_only')
    stdout_logging.setLevel(logging.INFO)
    stdout_logging.addHandler(handler)
    stdout_logging.propagate = False

    deku=Deku(config=config, 
            config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    router_mode = config['GATEWAY']['route_mode']
    router_phonenumber = config['GATEWAY']['router_phonenumber']

    url = config['GATEWAY']['route_url']
    priority_offline_isp = config['GATEWAY']['route_isp']
    router = Router(url=url, priority_offline_isp=priority_offline_isp, 
            config=config, config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    global routing_thread
    global routing_consume_connection, routing_consume_channel
    try:
        routing_consume_connection, routing_consume_channel = rabbitmq_connection(config)
        routing_thread = threading.Thread(target=routing_consume_channel.start_consuming)
        routing_thread.start()

        manage_modems(config, config_event_rules, config_isp_default, config_isp_operators)
        logging.info("listening for incoming messages")

    except pika.exceptions.ConnectionClosedByBroker as error:
        logging.critical(error)
        logging.info("Shutting down")
        exit(0)

if __name__ == "__main__":
    main()
