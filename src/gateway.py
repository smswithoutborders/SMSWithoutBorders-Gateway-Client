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

from deku import Deku
from mmcli_python.modem import Modem
from enum import Enum

from common.CustomConfigParser.customconfigparser import CustomConfigParser
from router import Router

# l_threads = {}
class Gateway(Router):

    def logger(self, text, _type='secondary', output='stdout', color=None, brightness=None):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        color='\033[32m'
        if output == 'stderr':
            color='\033[31m'
        if _type=='primary':
            print(color + timestamp + f'* [{self.m_isp}|{self.m_index}] {text}')
        else:
            print(color + timestamp + f'\t* [{self.m_isp}|{self.m_index}] {text}')
        print('\x1b[0m')

    def create_channel(self, connection_url, queue_name, exchange_name=None, exchange_type=None, durable=False, binding_key=None, callback=None, prefetch_count=0, connection_port=5672):
        credentials=None
        try:
            # TODO: port should come from config
            # parameters=pika.ConnectionParameters(connection_url, 5672, '/', credentials)
            parameters=pika.ConnectionParameters(connection_url, connection_port, '/')
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
        except pika.exceptions.ConnectionClosedByBroker as error:
            raise(error)
        except pika.exceptions.AMQPChannelError as error:
            # self.logger("Caught a chanel error: {}, stopping...".format(error))
            raise(error)
        except pika.exceptions.AMQPConnectionError as error:
            # self.logger("Connection was closed, should retry...")
            raise(error)
        except socket.gaierror as error:
            # print(error.__doc__)
            # print(type(error))
            # print(error)
            # if error == "[Errno -2] Name or service not known":
            raise(error)


    def __init__(self, m_index, m_isp, config, url, priority_offline_isp, ssl=None):
        super().__init__(url=url, priority_offline_isp=priority_offline_isp, ssl=ssl)
        self.m_index = m_index
        self.m_isp = m_isp
        self.config = config

        try:
            self.routing_consume_connection, self.routing_consume_channel = self.create_channel(
                    connection_url=config['GATEWAY']['connection_url'],
                    callback=self.__sms_routing_callback,
                    durable=True,
                    prefetch_count=1,
                    queue_name=config['GATEWAY']['routing_queue_name'])
        except pika.exceptions.ConnectionClosedByBroker:
            raise(error)
        except pika.exceptions.AMQPChannelError as error:
            # self.logger("Caught a chanel error: {}, stopping...".format(error))
            raise(error)
        except pika.exceptions.AMQPConnectionError as error:
            # self.logger("Connection was closed, should retry...")
            raise(error)
        except socket.gaierror as error:
            # print(error.__doc__)
            # print(type(error))
            # print(error)
            # if error == "[Errno -2] Name or service not known":
            raise(error)


    def __watchdog_incoming(self):
        # print('restart watchdog...')
        try:
            publish_connection, publish_channel = self.create_channel(
                    connection_url=config['GATEWAY']['connection_url'],
                    queue_name=config['GATEWAY']['routing_queue_name'],
                    durable=True)


            self.logger('watchdog incoming gone into effect...')
            # messages=Modem(self.m_index).SMS.list('received')

            modem = Modem(self.m_index)
            while(Deku.modem_ready(self.m_index)):
                # self.logger('checking for incoming messages...')
                messages=modem.SMS.list('received')
                for msg_index in messages:
                    sms=Modem.SMS(index=msg_index)


                    ''' should this message be deleted or left '''
                    ''' if deleted, then only the same gateway can send it further '''
                    ''' if not deleted, then only the modem can send the message '''
                    ''' given how reabbit works, the modem can't know when messages are sent '''
                    msg=f"Publishing {msg_index} for routing..."
                    self.logger(msg)
                    publish_channel.basic_publish(
                            exchange='',
                            routing_key=config['GATEWAY']['routing_queue_name'],
                            body=json.dumps({"text":sms.text, "number":sms.number}),
                            properties=pika.BasicProperties(
                                delivery_mode=2))
                    ''' delete messages from here '''
                    ''' use mockup so testing can continue '''
                    # self.logger(f"Published...")
                    # modem.delete(msg_index)

                messages=[]

                time.sleep(int(config['MODEMS']['sleep_time']))

        except Exception as error:
            # raise Exception(error)
            # self.logger(error)
            log_trace(traceback.format_exc())

        try:
            self.logger("watchdog incoming: Closing node...", output='stderr')

            # self.routing_consume_channel.stop_consuming()
            self.routing_consume_connection.close(reply_code=1, reply_text='modem no longer available')
        except Exception as error:
            # raise Exception(error)
            # self.logger(error)
            log_trace(traceback.format_exc())
        finally:
            ''' this finally because when connection is closed
            an exception is thrown '''
            if self.m_index in l_threads:
                del l_threads[self.m_index]

        ''' do whatever is required to cleanly end this node '''

    def __watchdog_monitor(self):
        '''
        - monitors state of modem, kills consumer if modem disconnects
        - checks for incoming messages and request
        '''

        try:
            self.logger('watchdog monitor gone into effect...')
            messages=Modem(self.m_index).SMS.list('received')
            while(Deku.modem_ready(self.m_index)):
                time.sleep(int(config['MODEMS']['sleep_time']))

        except Exception as error:
            # raise Exception(error)
            # self.logger(error)
            log_trace(traceback.format_exc())
        finally:
            # modem is no longer available
            try:
                self.logger("watchdog monitor: Closing node...", output='stderr')

                # self.outgoing_channel.stop_consuming()
                self.outgoing_connection.close(reply_code=1, reply_text='modem no longer available')
            except Exception as error:
                # raise Exception(error)
                # self.logger(error)
                log_trace(traceback.format_exc())
            finally:
                ''' this finally because when connection is closed
                an exception is thrown '''
                if self.m_index in l_threads:
                    del l_threads[self.m_index]

            ''' do whatever is required to cleanly end this node '''

    def start_consuming(self):
        # wd = threading.Thread(target=self.__watchdog, daemon=True)
        ''' starts watchdog to check if modem is still plugged in '''
        wd = threading.Thread(target=self.__watchdog_incoming, daemon=True)
        wd.start()

        self.logger('routing: waiting for message...')
        try:
            ''' messages to be routed '''
            self.logger('routing consumption starting...')
            self.routing_consume_channel.start_consuming() #blocking
            wd.join()

        except pika.exceptions.ConnectionWrongStateError as error:
            # self.logger(f'Request from Watchdog - \n\t {error}', output='stderr')
            log_trace(traceback.format_exc())
        except pika.exceptions.ChannelClosed as error:
            # self.logger(f'Request from Watchdog - \n\t {error}', output='stderr')
            log_trace(traceback.format_exc())
        except Exception as error:
            # self.logger(f'{self.me} Generic error...\n\t {error}', output='stderr')
            log_trace(traceback.format_exc())
        finally:
            del l_threads[self.m_index]

        # self.logger('ending consumption....')


    def __sms_routing_callback(self, ch, method, properties, body):
        json_body = json.loads(body.decode('unicode_escape'))
        self.logger(f'routing: {json_body}')
        # ch.basic_ack(delivery_tag=method.delivery_tag)

        ''' attempts both forms of routing, then decides if success or failed '''
        ''' checks config if for which state of routing is activated '''
        ''' if online only, if offline only, if both '''
        ''' also looks into which means of routing has been made available (which ISP if offline) '''
        # if Router.route( body.decode('utf-8')):
        if not "text" in json_body:
            log_trace('poorly formed message - text missing')
            ''' acks so that the message does not go back to the queue '''
        if not "number" in json_body:
            log_trace('poorly formed message - number missing')
            ''' acks so that the message does not go back to the queue '''
        try:
            results=None
            json_data = json.dumps({"text":json_body['text'], "number":json_body['number']})
            # router = self.Router(url=self.config['ROUTER']['default'], priority_offline_isp=self.config['ROUTER']['isp'])
            if self.config['GATEWAY']['route_mode'] == self.Modes.ONLINE.value:
                results = self.route_online(data=json_data)
                self.logger(f"Routing results (ONLINE): {results.text} {results.status_code}")


            elif self.config['GATEWAY']['route_mode'] == self.Modes.OFFLINE.value:
                results = self.route_offline(text=json_body['text'], number=json_body['number'])
                self.logger(f"Routing results (OFFLINE): {results}")


            elif self.config['GATEWAY']['route_mode'] == self.Modes.SWITCH.value:
                try:
                    results = self.route_online(data=json_data)
                    self.logger(f"Routing results (SWITCH|ONLINE): {results}")

                except Exception as error:
                    try:
                        results = self.route_offline(text=json_body['text'], number=json_body['number'])
                        self.logger(f"Routing results (SWITCH|OFFLINE): {results}")
                    except Exception as error:
                        # raise Exception(error)
                        log_trace(traceback.format_exc())
                        raise(error)
            else:
                self.logger(f"Invalid routing protocol", output="stderr")

            ''' acks that the message has been received (routed) '''
            self.routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
        except self.MissingComponent as error:
            # print(error)
            ''' ack so that the messages don't go continue queueing '''
            self.routing_consume_channel.basic_ack(delivery_tag=method.delivery_tag)
            log_trace(traceback.format_exc(), show=True)
        except ConnectionError as error:
            '''
            In the event of a network problem (e.g. DNS failure, refused connection, etc), Requests will raise a ConnectionError exception.
            '''
            self.routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
        except requests.Timeout as error:
            '''
            If a request times out, a Timeout exception is raised.
            '''
            self.routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
        except requests.TooManyRedirects as error:
            '''
            If a request exceeds the configured number of maximum redirections, a TooManyRedirects exception is raised.
            '''
            self.routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
        except Exception as error:
            self.routing_consume_channel.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
            log_trace(traceback.format_exc(), show=True)

def log_trace(text, show=False, output='stdout', _type='primary'):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(os.path.join(os.path.dirname(__file__), 'service_files/logs', 'logs_node.txt'), 'a') as log_file:
        log_file.write(timestamp + " " +text + "\n\n")

    if show:
        color='\033[32m'
        if output == 'stderr':
            color='\033[31m'
        if _type=='primary':
            print(color + timestamp + f'* {text}')
        else:
            print(color + timestamp + f'\t* {text}')
        print('\x1b[0m')

def master_watchdog(config):
    shown=False
    global l_threads
    l_threads={}

    ''' instantiate configuration for all of Deku '''
    try:
        Deku()
        # configreader=CustomConfigParser()
        # config_event_rules=configreader.read("configs/events/rules.ini")
    except CustomConfigParser.NoDefaultFile as error:
        raise(error)
    except CustomConfigParser.ConfigFileNotFound as error:
        raise(error)
    except CustomConfigParser.ConfigFileNotInList as error:
        raise(error)
    else:
        while( True ):
            indexes=[]
            try:
                # indexes=Deku.modems_ready(ignore_lock=True)
                # indexes=Deku.modems_ready(remove_lock=True, ignore_lock=True)
                indexes=Deku.modems_ready(remove_lock=True)
                # indexes=['1', '2']
            except Exception as error:
                log_trace(error)
                continue

            if len(indexes) < 1:
                # print(colored('* waiting for modems...', 'green'))
                if not shown:
                    print('* No Available Modem...')
                    shown=True
                time.sleep(int(config['MODEMS']['sleep_time']))
                continue

            shown=False
            # print('[x] starting consumer for modems with indexes:', indexes)
            for m_index in indexes:
                '''starting consumers for modems not already running,
                should be a more reliable way of doing it'''
                if m_index not in l_threads:
                    country=config['ISP']['country']
                    if not Deku.modem_ready(m_index):
                        continue
                    try:
                        m_isp = Deku.ISP.modems(operator_code=Modem(m_index).operator_code, country=country)
                    except Exception as error:
                        # print(error)
                        log_trace(error, show=True)
                        continue

                    try:
                        gateway=Gateway(m_index=m_index, m_isp=m_isp, config=config, url=config['ROUTER']['default'], priority_offline_isp=config['ROUTER']['isp'])
                        # print(outgoing_node, outgoing_node.__dict__)
                        gateway_thread=threading.Thread(target=gateway.start_consuming, daemon=True)

                        # l_threads[m_index] = [outgoing_thread, routing_thread]
                        l_threads[m_index] = [gateway_thread]
                        # print('\t* Node created')
                    except pika.exceptions.ConnectionClosedByBroker:
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except pika.exceptions.AMQPChannelError as error:
                        # self.logger("Caught a chanel error: {}, stopping...".format(error))
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except pika.exceptions.AMQPConnectionError as error:
                        # self.logger("Connection was closed, should retry...")
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except socket.gaierror as error:
                        # print(error.__doc__)
                        # print(type(error))
                        # print(error)
                        # if error == "[Errno -2] Name or service not known":
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except CustomConfigParser.NoDefaultFile as error:
                        # print(traceback.format_exc())
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except CustomConfigParser.ConfigFileNotFound as error:
                        ''' with this implementation, it stops at the first exception - intended?? '''
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except CustomConfigParser.ConfigFileNotInList as error:
                        log_trace(traceback.format_exc(), output='stderr', show=True)
                    except Exception as error:
                        log_trace(traceback.format_exc(), output='stderr', show=True)

                    shown=False

            try:
                for m_index, thread in l_threads.items():
                    try:
                        # if not thread in threading.enumerate():
                        for i in range(len(thread)):
                            if thread[i].native_id is None:
                                print('\t* starting thread...')
                                thread[i].start()

                    except Exception as error:
                        log_trace(traceback.format_exc(), show=True)
            except Exception as error:
                log_trace(error)

            time.sleep(int(config['MODEMS']['sleep_time']))


if __name__ == "__main__":
    ''' checks for incoming messages and routes them '''
    config=None
    config=CustomConfigParser()
    config=config.read(".configs/config.ini")

    master_watchdog(config)
    exit(0)
