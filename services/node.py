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
import subprocess
import json, time
from datetime import datetime

from colorama import init
from termcolor import colored

from configparser import ConfigParser, ExtendedInterpolation

import pika

sys.path.append(os.path.abspath(os.getcwd()))
from deku import Deku
from mmcli_python.modem import Modem


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
    def logger(self, text, _type='secondary', output='stdout', color=None, brightness=None):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        color='\033[32m'
        if output == 'stderr':
            color='\033[31m'
        if _type=='primary':
            print(color + timestamp + f'* {self.me} {text}')
        else:
            print(color + timestamp + f'\t* {self.me} {text}')
        print('\x1b[0m')

    '''
    expected inputs should be what events this node subscribes to
    this can be defined in rules and defaulted as shown below
    '''
    # def __init__(self, m_index, m_isp, rules=['STATUS']):
    def __init__(self, m_index, m_isp):
        self.previousError=None
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        try:
            connection_url = config['NODE']['connection_url']
            self.connection=pika.BlockingConnection(pika.ConnectionParameters(connection_url))
        except Exception as error:
            # raise Exception(traceback.format_exc())
            raise Exception(error)
            # sys.exit(1)
        else:
            # self.logger("connection established!")
            color='\033[32m'
            print(color + timestamp + f'\t* [{m_index}] connection established')

        self.m_index=m_index
        self.me = f'[{self.m_index}]'

        self.exchange=config['NODE']['exchange_name']
        self.exchange_type=config['NODE']['exchange_type'] 

        self.sms_outgoing_channel=self.connection.channel()
        # self.sms_outgoing_channel.exchange_declare(exchange=self.exchange, exchange_type=self.exchange_type)

        ''' format=<dev id>.<isp> '''
        self.queue_name=f"{config['NODE']['queue_name']}_{m_isp}"
        self.sms_outgoing_channel.queue_declare(self.queue_name)

        ''' listens to all request coming for specific isp '''
        ''' with the default binding key, it receives all messages '''
        self.binding_key=self.queue_name.replace('_', '.')


        try:

            self.logger(f'binding key: {self.binding_key}')
            self.sms_outgoing_channel.queue_bind(
                    exchange=self.exchange, 
                    queue=self.queue_name, 
                    routing_key=self.binding_key)

        except pika.exceptions.ChannelClosedByBroker as error:
            # raise Exception(traceback.format_exc())
            # raise Exception(error)
            # sys.exit(1)
            '''
            self.logger(error, output='stderr')
            raise Exception(error)
            '''
            log_trace(traceback.format_exc())
        except Exception as error:
            # raise Exception(traceback.format_exc())
            # raise Exception(error)
            # sys.exit(1)
            '''
            self.logger(f'Generic error:\n\t{error}', output='stderr')
            raise Exception(error)
            '''
            log_trace(traceback.format_exc())

        ''' consumer properties '''
        ''' no auto_ack '''

        # TODO: delete this, ack should be manual
        try:
            '''
            self.sms_outgoing_channel.basic_consume(
                    queue=self.queue_name, 
                    on_message_callback=self.__sms_outgoing_callback, 
                    auto_ack=bool(int(config['NODE']['auto_ack'])))
            '''
            self.sms_outgoing_channel.basic_consume(
                    queue=self.queue_name, 
                    on_message_callback=self.__sms_outgoing_callback)
        except pika.exceptions.ChannelWrongStateError as error:
            '''
            self.logger(error, output='stderr')
            raise Exception(error)
            '''
            log_trace(traceback.format_exc())
        except Exception as error:
            '''
            self.logger(f'Generic error:\n\t{error}', output='stderr')
            raise Exception(error)
            '''
            log_trace(traceback.format_exc())



        ''' set fair dispatch '''
        self.sms_outgoing_channel.basic_qos(prefetch_count=int(config['NODE']['prefetch_count']))


        def generate_status_file(status):
            ''' all the categories should be fitted here '''
            status['BECHMARK'] = {"counter":0}

            return status

        self.status_file=os.path.join(
                os.path.dirname(__file__), 
                'status', 
                f'{Modem(self.m_index).imei}.ini')
        if not os.path.isfile(self.status_file):
            # self.logger('event rules for modem found')
            with open(self.status_file, 'w') as sf:
                status=ConfigParser()
                status=generate_status_file(status)
                status.write(sf)
                self.logger('event rules created')

    '''
    nodes can receive different kinds of messages,
    so different types of callbacks to handle them
    '''

    def __sms_outgoing_callback(self, ch, method, properties, body):

        ''' update_status -> this should work for multiple datatypes '''
        def update_status(category, status):
            # status_file=os.path.join(os.path.dirname(__file__), 'status', f'{Modem(self.m_index).imei}.ini')
            self.logger(f'updating status.... {self.status_file}')
            status=ConfigParser()
            status=status.read(self.status_file)
            if category == 'BENCHMARK':
                status_counter=int(status[category]['COUNTER'])
                with open(self.status_file, 'w') as st_file:
                    if not 'BENCHMARK' in event_config.sections():
                        status['BENCHMARK'] = {}
                    if status == 0:
                        status['BENCHMARK']['counter'] = 0
                    elif status == 1:
                        status['BENCHMARK']['counter'] = status_counter + 1
                    else:
                        raise exception('unknown status')
                    status.write(st_file)
                    self.logger('log file written....')

        # TODO: verify data coming in is actually a json
        json_body = json.loads(body.decode("utf-8"))
        self.logger(f'message: {json_body}')

        '''
        text - message to send
        number - receipient number
        '''
        ''' raising exceptions here crashes the consumer loop, just output it for now '''
        if not "text" in json_body:
            # raise KeyError
            log_trace('poorly formed message - text missing')
            return 
        
        if not "number" in json_body:
            log_trace('poorly formed message - number missing')
            return 
        '''
        - When messages are rejected they are returned back immediately
        - So rejection without further consumers to consume means a loop
        is created
        '''

        text=json_body['text']
        number=json_body['number']
        status=1

        try:
            self.logger('sending sms...')
            Deku.send(text=text, number=number)

        except Deku.InvalidNumber as error:
            ''' wrong number: message does not comes back '''
            self.logger(f'{error.message} - {error.number}')
            log_trace(error.message)
            self.sms_outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
            self.logger('sending sms failed...', output='stderr')
        except Deku.NoAvailableModem as error:
            ''' no available modem: message comes back '''
            if self.previousError != error.message:
                log_trace(error.message)
                self.logger(error.message)

            self.previousError = error.message
            ''' block this and before rejecting to avoid the loop '''

            self.logger('sending sms failed...', output='stderr')
            ''' blocks the connection '''
            # TODO: add from configs

            self.sms_outgoing_channel.basic_reject(
                    delivery_tag=method.delivery_tag, 
                    requeue=True)
            self.connection.sleep(5)

        except subprocess.CalledProcessError as error:
            ''' generic system error: message comes back '''
            ''' requires further processing '''
            self.logger('sending sms failed...', output='stderr')
            # self.logger(error.output, ot)
            # self.logger(error.stdout)
            log_trace(error.output)
            self.sms_outgoing_channel.basic_reject(
                    delivery_tag=method.delivery_tag, 
                    requeue=True)
            '''node keeps track of this failures, and send message to 
            server after a benchmark failed limit
            '''
            '''
            options here---
            -> open up connection and remotely send USSD request - manual intervention
            -> 
            # with open(os.path.join(os.path.dirname(__file__), 'locks', f'{Modem(m_index).imei}.ini'), 'w') as log_file:
            '''
            category='BENCHMARK'
            update_status(category, status)
            self.__event_watch(category)


        except Exception as error:
            ''' code crashed here '''
            self.logger('sending sms failed...', output='stderr')
            log_trace(traceback.format_exc())
            self.sms_outgoing_channel.basic_reject(
                    delivery_tag=method.delivery_tag, 
                    requeue=True)
        else:
            ''' message ack happens here '''
            ''' after successful delivery, pause for a bit before continuing '''
            self.sms_outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
            self.logger('message sent successfully')

            ''' 0 = success '''
            category='BENCHMARK'
            variable='counter'
            status=0
            update_status(category, status)


    def __event_action_run(self):
        '''
        '''
        self.logger(f'event listener taking action: {action}')

    def __event_watch(self, category):
        ''' case:BENCHMARK '''
        if category == 'BENCHMARK':
            '''
            compare benchmark_limit(input) to current_status
            '''

            benchmark_limit=int(config['MODEMS']['benchmark_limit'])
            status=ConfigParser()
            status=status.read(self.status_file)

            ''' COUNTER = is respective to BENCHMAKR '''
            current_status=int(status[category]['counter'])


            command=status[category]['CONDITION']

            if command == '">"':
                if current_status > benchmark_limit:
                    ''' action should be passed in here '''
                    self.__event_action_run()

            ''' other options go here '''
        else:
           raise Exception('unknown category')

    def __watchdog(self, m_id=None, status=None):
        '''
        - monitors state of modem, kills consumer if modem disconnects
        '''
        try:
            self.logger('watchdog gone into effect...')
            while(Deku.modem_ready(self.m_index)):
                time.sleep(int(config['MODEMS']['sleep_time']))
        except Exception as error:
            # raise Exception(error)
            # self.logger(error)
            log_trace(traceback.format_exc())
        finally:
            # modem is no longer available
            try:
                self.sms_outgoing_channel.stop_consuming()
                self.connection.close(reply_code=1, reply_text='modem no longer available')
            except Exception as error:
                # raise Exception(error)
                # self.logger(error)
                log_trace(traceback.format_exc())

            ''' do whatever is required to cleanly end this node '''


    def start_consuming(self):
        self.logger('waiting for message...')

        # wd = threading.Thread(target=self.__watchdog, daemon=True)
        wd = threading.Thread(target=self.__watchdog)
        wd.start()
        try:
            self.sms_outgoing_channel.start_consuming()
        except pika.exceptions.ConnectionWrongStateError as error:
            # self.logger(f'Request from Watchdog - \n\t {error}', output='stderr')
            log_trace(traceback.format_exc())
        except pika.exceptions.ChannelClosed as error:
            # self.logger(f'Request from Watchdog - \n\t {error}', output='stderr')
            log_trace(traceback.format_exc())
        except Exception as error:
            # self.logger(f'{self.me} Generic error...\n\t {error}', output='stderr')
            log_trace(traceback.format_exc())

def log_trace(text, show=False, output='stdout', _type='primary'):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(os.path.join(os.path.dirname(__file__), 'log_trace', 'logs_node.txt'), 'a') as log_file:
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

def master_watchdog():
    shown=False
    while( True ):
        indexes=[]
        try:
            indexes=Deku.modems_ready()
            # indexes=['1', '2']
        except Exception as error:
            log_trace(error)
            continue

        if not shown and len(indexes) < 1:
            # print(colored('* waiting for modems...', 'green'))
            print('* waiting for modems...')
            shown=True
            time.sleep(int(config['MODEMS']['sleep_time']))
            continue

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

                '''
                if m_isp is None:
                    continue
                '''

                print('\t* starting consumer for:', m_index, m_isp)
                try:
                    node=Node(m_index, m_isp)
                    thread=threading.Thread(target=node.start_consuming, daemon=True)
                    l_threads[m_index] = thread
                except Exception as error:
                    log_trace(traceback.format_exc(), show=True)

            elif m_index in l_threads and not l_threads[m_index].is_alive():
                ''' policing to make sure all threads are alive and working '''
                del l_threads[m_index]

        for m_index, thread in l_threads.items():
            try:
                # if not thread in threading.enumerate():
                if thread.native_id is None:
                    thread.start()
            except Exception as error:
                log_trace(traceback.format_exc(), show=True)

        time.sleep(int(config['MODEMS']['sleep_time']))

if __name__ == "__main__":
    print('* master watchdog booting up')
    master_watchdog()

