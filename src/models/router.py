#!/usr/bin/env python3

'''
- messages are routed using rabbitmq
- the receiver holds the routing service '''


import json
import requests
import logging
from enum import Enum
from deku import Deku

class Router(Deku):
    class Modes(Enum):
        OFFLINE='0'
        ONLINE='1'
        SWITCH='2'

    class MissingComponent(Exception):
        def __init__(self, component):
            self.component = component

    ssl = None
    # def __init__(self, cert, key):
    def __init__(self, url, priority_offline_isp, config, config_isp_default, config_isp_operators, ssl=None):
        super().__init__(config, config_isp_default, config_isp_operators)
        self.ssl = ssl 
        self.url = url
        self.priority_offline_isp = priority_offline_isp


    def route_offline(self, text, number):
        logging.debug(text)
        try:
            self.send(
                    text=text,
                    number=number,
                    number_isp=False,
                    isp=self.priority_offline_isp)
        except self.NoAvailableModem as error:
            raise error
        except Exception as error:
            raise error


    def route_online(self, data, protocol='POST', url=None):
        print(f"* routing online {data} {protocol}")
        results=None
        is_json=False

        ''' test if json '''
        try:
            data = json.loads(data)
            is_json=True
        except ValueError as error:
            pass

        try:
            if protocol == 'GET': 
                if is_json:
                    if self.ssl is not None:
                        results = requests.get(self.url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(self.url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.get(self.url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(self.url, data=data)


            if protocol == 'POST': 
                if is_json:
                    if self.ssl is not None:
                        results = requests.post(self.url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(self.url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.post(self.url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(self.url, data=data)

        except ConnectionError as error:
            '''
            In the event of a network problem (e.g. DNS failure, refused connection, etc), Requests will raise a ConnectionError exception.
            '''
            raise ConnectionError(error)

        except requests.Timeout as error:
            '''
            If a request times out, a Timeout exception is raised.
            '''
            raise request.Timeout(error)

        except requests.TooManyRedirects as error:
            '''
            If a request exceeds the configured number of maximum redirections, a TooManyRedirects exception is raised.
            '''
            raise requests.TooManyRedirects(error)

        return results



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

def incoming_listener():
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

    try:
        routing_consume_connection, routing_consume_channel = rabbitmq_connection(config)

        routing_thread = threading.Thread(
                target=routing_consume_channel.start_consuming, daemon=True)

        # route listener begins here
        routing_thread.start()

        # if manage_modems dies - incoming listeners die
        """
        manage_modems(config, config_event_rules, 
                config_isp_default, config_isp_operators)
        """

    except pika.exceptions.ConnectionClosedByBroker as error:
        logging.critical(error)

if __name__ == "__main__":
    data=json.dumps({"text":"Hello world", "number":"0000"})
    router = Router(url='http://localhost:6969', priority_offline_isp='orange')
    # router.route_online(data=data)
    results = router.route_online(data=data, protocol='POST')
    print(results.text, results.status_code)
