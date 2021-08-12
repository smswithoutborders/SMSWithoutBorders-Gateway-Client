#!/usr/bin/python3

''' testing criterias----
- when modem is present a node should start up
    - should be able to receive messages from a producer
'''

''' protocol
- queues hold messages
- nodes listen on queues
- messages are routed to queues from exchanges

- gateway states
    - online -> messages come directly from server (this is the case we're looking at)
    - offline -> messages come from sms services like Twilio

- user_id:user_key = exchange
- nodes id becomes topics to listen to

<issues aren't what the nodes want to hear, but what the clients are sending>

## exchange and queue should be static and known only to the host
exchange_name="DEKU_CLUSTER"
queue_name="OUTGOING_SMS"

exchange_name = <would depend on the server configuration>
queue_name = <would depend on the server configuration>

exchange type: topic
topic methods
-> 12345.1a2b3c.MTN
-> dev_id.node_id.isp
'''

''' TODO <lookup>:
- authenticate nodes when connecting
- make sure messages are not persistent
- stop nodes from declaring exchange and queues
'''

import sys, os, threading, traceback
import asyncio
import json, time

from colorama import init
from termcolor import colored

from configparser import ConfigParser, ExtendedInterpolation

import pika

sys.path.append(os.path.abspath(os.getcwd()))
from deku import Deku
from mmcli_python.modem import Modem


connection=None
config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))

''' 
- monitor for modem comes and goes
- matching with index, because if index changes, the consumer should restart
or update adequately... tho not sure if to just restart or update'''
l_threads={}

'''
initialize term colors
'''
init()

class Node:
    def logger(self, text, _type='secondary', color=None, brightness=None):
        if _type=='primary':
            print('\033[32' + f'* {self.me} {text}')
            print('\x1b[0m')
        else:
            print('\033[32;1m' + f'\t* {self.me} {text}')
            print('\x1b[0m')

    def __init__(self, m_index, m_isp):
        try:
            connection_url = config['NODE']['connection_url']
            connection=pika.BlockingConnection(pika.ConnectionParameters(connection_url))
        except Exception as error:
            print(traceback.format_exc())
            sys.exit(1)

        ''' 
        queue_name : should be name of isp - no cus this would delete the entirty when 
        closed
        '''
        self.m_index=m_index
        self.me = f'[{self.m_index}]'

        self.exchange=config['NODE']['exchange_name']
        self.queue_name=config['NODE']['queue_name']
        self.binding_key=f"{config['NODE']['binding_key']}.{m_isp}"
        self.sms_outgoing_channel=connection.channel()

        ''' bind queue to exchange '''
        try:

            self.logger(f'binding key: {self.binding_key}')
            self.sms_outgoing_channel.queue_bind(
                    exchange=self.exchange, 
                    queue=self.queue_name, 
                    routing_key=self.binding_key)

        except pika.exceptions.ChannelClosedByBroker as error:
            self.logger(error)
            sys.exit(1)
        except Exception as error:
            self.logger(traceback.format_exc())
            sys.exit(1)

        ''' consumer properties '''
        ''' no auto_ack '''

        # TODO: delete this, ack should be manual
        self.sms_outgoing_channel.basic_consume(
                queue=self.queue_name, 
                on_message_callback=self.__sms_outgoing_callback, 
                auto_ack=bool(int(config['NODE']['auto_ack'])))

        '''
        self.sms_outgoing_channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.__callback)
        '''

        ''' set fair dispatch '''
        self.sms_outgoing_channel.basic_qos(prefetch_count=int(config['NODE']['prefetch_count']))

    '''
    nodes can receive different kinds of messages,
    so different types of callbacks to handle them
    '''

    def __sms_outgoing_callback(self, ch, method, properties, body):
        # TODO: verify data coming in is actually a json
        json_body = json.loads(body.decode("utf-8"))
        self.logger(f'message: {json_body}')

    def __watchdog(self):
        self.logger('watchdog gone into effect...')
        '''
        monitors state of modem, kills consumer if modem disconnects
        '''
        while(Deku.modem_ready(self.m_index)):
            time.sleep(int(config['MODEMS']['sleep_time']))

        ''' modem is no longer available '''
        self.sms_outgoing_channel.close(reply_code=1, reply_text='modem no longer available')

        ''' do whatever is required to cleanly end this node '''


    def start_consuming(self):
        self.logger('waiting for message...')

        wd = threading.Thread(target=self.__watchdog, daemon=True)
        wd.start()
        try:
            self.sms_outgoing_channel.start_consuming()
        except pika.exceptions.ConnectionWrongStateError as error:
            self.logger(f'Request from Watchdog - \n  {error}')
        except Exception as error:
            self.logger(f'{self.me} Generic error...\n  {error}')
        finally:
            del l_thread[self.index]

def master_watchdog():
    shown=False
    while( True ):
        indexes=Deku.modems_ready()
        # indexes=['1', '2']

        if not shown and len(indexes) < 1:
            # print(colored('* waiting for modems...', 'green'))
            print('\033[32;1m' + '* waiting for modems...')
            print('\x1b[0m')
            shown=True
            time.sleep(int(config['MODEMS']['sleep_time']))
            continue

        # print('[x] starting consumer for modems with indexes:', indexes)
        for m_index in indexes:
            '''starting consumers for modems not already running,
            should be a more reliable way of doing it'''
            if m_index not in l_threads:
                country=config['ISP']['country']
                m_isp = Deku.ISP.modems(operator_code=Modem(m_index).operator_code, country=country)

                print('\t* starting consumer for:', m_index, m_isp)
                node=Node(m_index, m_isp)

                thread=threading.Thread(target=node.start_consuming, daemon=True)
                l_threads[m_index] = thread

        for m_index, thread in l_threads.items():
            if not thread.is_alive():
                thread.start()

        time.sleep(int(config['MODEMS']['sleep_time']))

if __name__ == "__main__":
    print('* master watchdog booting up')
    master_watchdog()

