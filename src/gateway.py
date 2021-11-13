#!/usr/bin/env python3

import time 
import os
import pika
import socket
import threading
import traceback
import json
import requests
from datetime import datetime
from base64 import b64encode

from deku import Deku
from mmcli_python.modem import Modem
from enum import Enum

from common.CustomConfigParser.customconfigparser import CustomConfigParser
from router import Router

# active_threads = {}
routing_consume_connection = None
routing_consume_channel = None
"""
publish_connection = None
publish_channel= None
"""

class Gateway(Router):

    def logger(self, text, _type='secondary', output='stdout', color=None, brightness=None):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
        color='\033[32m'
        if output == 'stderr':
            color='\033[31m'
        if _type=='primary':
            print(color + timestamp + f'* [{self.m_isp}|{self.modem_index}] {text}')
        else:
            print(color + timestamp + f'\t* [{self.m_isp}|{self.modem_index}] {text}')
        print('\x1b[0m')



    def __init__(self, modem_index, m_isp, config, url, priority_offline_isp, 
            config_isp_default, config_isp_operators, ssl=None):

        super().__init__(url=url, priority_offline_isp=priority_offline_isp, 
                ssl=ssl, config=config, config_isp_default=config_isp_default, 
                config_isp_operators=config_isp_operators)
        self.modem_index = modem_index
        self.m_isp = m_isp
        self.config = config


    def watchdog_incoming(self):
        while(Deku.modem_ready(self.modem_index)):
            # self.logger('checking for incoming messages...')
            messages=Modem(self.modem_index).SMS.list('received')
            publish_connection, publish_channel = create_channel(
                    connection_url=config['GATEWAY']['connection_url'],
                    queue_name=config['GATEWAY']['routing_queue_name'],
                    blocked_connection_timeout=300,
                    durable=True)
            for msg_index in messages:
                sms=Modem.SMS(index=msg_index)


                ''' should this message be deleted or left '''
                ''' if deleted, then only the same gateway can send it further '''
                ''' if not deleted, then only the modem can send the message '''
                ''' given how reabbit works, the modem can't know when messages are sent '''
                msg=f"Publishing {msg_index}"
                self.logger(msg)
                try:
                    # routing_consume_channel.basic_publish(
                    publish_channel.basic_publish(
                            exchange='',
                            routing_key=config['GATEWAY']['routing_queue_name'],
                            body=json.dumps({"text":sms.text, "phonenumber":sms.number}),
                            properties=pika.BasicProperties(
                                delivery_mode=2))
                    ''' delete messages from here '''
                    ''' use mockup so testing can continue '''
                    # self.logger(f"Published...")
                except Exception as error:
                    log_trace(traceback.format_exc())
                else:
                    try:
                        Modem(self.modem_index).SMS.delete(msg_index)
                    except Exception as error:
                        log_trace(traceback.format_exc(), show=True)

            messages=[]

            time.sleep(int(config['MODEMS']['sleep_time']))
        self.logger("disconnected", output='stderr') 
        if self.modem_index in active_threads:
            del active_threads[self.modem_index]



def init_nodes(indexes, config, config_isp_default, config_isp_operators, config_event_rules):
    isp_country = config['ISP']['country']
    deku=Deku(config=config, 
            config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)
    for modem_index in indexes:
        if modem_index not in active_nodes:
            if not deku.modem_ready(modem_index):
                continue
            try:
                modem_isp = deku.ISP.modems(
                        operator_code=Modem(modem_index).operator_code, 
                        country=isp_country)

                gateway=Gateway(modem_index, m_isp, config, url, priority_offline_isp, 
                        config_isp_default, config_isp_operators)
                gateway_thread=threading.Thread(
                        target=node.start_consuming, daemon=True)

                active_nodes[modem_index] = [gateway_thread, gateway]

            except Exception as error:
                raise(error)

def start_nodes():
    for modem_index, thread_n_node in active_nodes.items():
        thread = thread_n_node[0]
        try:
            if thread.native_id is None:
                thread.start()

        except Exception as error:
            raise(error)

def manage_modems(config, config_event_rules, config_isp_default, config_isp_operators):
    global active_nodes
    active_nodes = {}
    sleep_time = int(config['MODEMS']['sleep_time']) if \
            int(config['MODEMS']['sleep_time']) > 3 else 3

    logging.info('modem manager started')
    while True:
        indexes=[]
        try:
            indexes=Deku.modems_ready(remove_lock=True)
            if len(indexes) < 1:
                stdout_logging.info("No modem available")
                time.sleep(sleep_time)
                continue

        except Exception as error:
            raise(error)
        
        try:
            init_nodes(indexes, config, config_isp_default, config_isp_operators, config_event_rules)
            start_nodes()
        except Exception as error:
            raise(error)
        time.sleep(sleep_time)


def route_online(data):
    results = router.route_online(data=data)
    print(f"Routing results (ONLINE): {results.text} {results.status_code}")

def route_offline(text, number):
    results = router.route_offline(text=text, number=number)
    print("* Routing results (OFFLINE) SMS successfully routed...")

def sms_routing_callback(ch, method, properties, body):
    json_body = json.loads(body.decode('unicode_escape'))
    print(f'routing: {json_body}')

    if not "text" in json_body:
        log_trace('poorly formed message - text missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    if not "phonenumber" in json_body:
        log_trace('poorly formed message - number missing')
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        results=None
        json_data = json.dumps(json_body)
        # text_body = body.decode('unicode_escape')
        '''
        body is transmitted in base64 and should be decoded at the receiving end
        '''
        body = str(b64encode(body), 'unicode_escape')
        router_phonenumber=config['ROUTER']['router_phonenumber']
        # router = self.Router(url=config['ROUTER']['default'], priority_offline_isp=config['ROUTER']['isp'])
        if config['GATEWAY']['route_mode'] == Router.Modes.ONLINE.value:
            route_online(json_data)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif config['GATEWAY']['route_mode'] == Router.Modes.OFFLINE.value:
            # results = router.route_offline(text=json_body['text'], number=router_phonenumber)
            route_offline(body, router_phonenumber)
            routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        elif config['GATEWAY']['route_mode'] == Router.Modes.SWITCH.value:
            try:
                route_online(json_data)
                routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as error:
                try:
                    route_offline(body, router_phonenumber)
                    routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as error:
                    # raise Exception(error)
                    log_trace(traceback.format_exc())
                    raise(error)
        else:
            print(f"Invalid routing protocol")
    except Router.MissingComponent as error:
        # print(error)
        ''' ack so that the messages don't go continue queueing '''
        routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        log_trace(traceback.format_exc())
    except ConnectionError as error:
        '''
        In the event of a network problem (e.g. DNS failure, refused connection, etc), Requests will raise a ConnectionError exception.
        '''
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
    except requests.Timeout as error:
        '''
        If a request times out, a Timeout exception is raised.
        '''
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
    except requests.TooManyRedirects as error:
        '''
        If a request exceeds the configured number of maximum redirections, a TooManyRedirects exception is raised.
        '''
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
    except Exception as error:
        routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
        log_trace(traceback.format_exc())
    finally:
        routing_consume_connection.sleep(3)

def create_channel(connection_url, queue_name, exchange_name=None, 
        exchange_type=None, durable=False, binding_key=None, callback=None, 
        prefetch_count=0, connection_port=5672, heartbeat=600, 
        blocked_connection_timeout=None):

    credentials=None
    try:
        parameters=pika.ConnectionParameters(
                connection_url, 
                connection_port, 
                '/', 
                heartbeat=heartbeat)

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
        raise(error)


def rabbitmq_connection(config):
    global routing_consume_connection
    global routing_consume_channel

    print("* starting rabbitmq connections... ", end="")
    connection_url=config['GATEWAY']['connection_url']
    queue_name=config['GATEWAY']['routing_queue_name']

    try:
        routing_consume_connection, routing_consume_channel = create_channel(
                connection_url=connection_url,
                callback=sms_routing_callback,
                durable=True,
                prefetch_count=1,
                queue_name=queue_name)

    except Exception as error:
        log_trace(traceback.format_exc())
    else:
        print("Done")

def start_consuming():
    try:
        print('routing consumption starting...')
        routing_consume_channel.start_consuming() #blocking

    except pika.exceptions.ConnectionWrongStateError as error:
        # print(f'Request from Watchdog - \n\t {error}', output='stderr')
        log_trace(traceback.format_exc())
    except pika.exceptions.ChannelClosed as error:
        # print(f'Request from Watchdog - \n\t {error}', output='stderr')
        log_trace(traceback.format_exc())
    except Exception as error:
        # print(f'{self.me} Generic error...\n\t {error}', output='stderr')
        log_trace(traceback.format_exc())
    finally:
        print("Stopped consuming...")

def main(config, config_event_rules, config_isp_default, config_isp_operators):
    url = config['ROUTER']['default']
    priority_offline_isp = config['ROUTER']['isp']
    router = Router(url=url, priority_offline_isp=priority_offline_isp, 
            config=config, config_isp_default=config_isp_default, 
            config_isp_operators=config_isp_operators)

    rabbitmq_connection(config)
    thread_rabbitmq_connection = threading.Thread(target=routing_consume_channel.start_consuming, daemon=True)
    thread_rabbitmq_connection.start()

    manage_modems(config, config_event_rules, config_isp_default, config_isp_operators)
    thread_rabbitmq_connection.join()

if __name__ == "__main__":
    main()
