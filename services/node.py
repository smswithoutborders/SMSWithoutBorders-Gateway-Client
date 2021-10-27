#!/usr/bin/env python3

import os
import threading
import traceback
import socket
# import asyncio
import subprocess
import json
import time
# import requests

from transmissionLayer import TransmissionLayer
''' testing criterias----
- when modem is present a node should start up
    - should be able to receive messages from a producer
'''

''' protocol
- queues hold messages
- nodes listen on queues
- messages are routed to queues from exchanges

- gateway states
    - online -> messages come directly from server
    (this is the case we're looking at)
    - offline -> messages come from sms services like Twilio

- user_id:user_key = exchange
- nodes id becomes topics to listen to <issues aren't what the nodes want to hear, but what the clients are sending>

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

from datetime import datetime
from enum import Enum

from colorama import init
# from termcolor import colored

# from configparser import configparser.ConfigParser, ExtendedInterpolation
import configparser
from CustomConfigParser.customconfigparser import CustomConfigParser

import pika

# sys.path.append(os.path.abspath(os.getcwd()))
from deku import Deku
from mmcli_python.modem import Modem


"""
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
"""


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
    m_index = None
    m_isp = None
    config = None

    outgoing_connection=None
    outgoing_channel=None

    previousError=None


    class Category(Enum):
        SUCCESS='SUCCESS'
        FAILED='FAILED'
        UNKNOWN='UNKNOWN'
        TRANSMISSION='TRANSMISSION'


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


    # def __init__(self, m_index, m_isp, rules=['STATUS']):
    # TODO: everything from config files should be externally sent and not read in the class
    def __init__(self, m_index, m_isp, config, config_event_rules):
        self.config_event_rules = config_event_rules
        self.config = config
        def create_channel(connection_url, queue_name, username=None, password=None, exchange_name=None, exchange_type=None, durable=False, binding_key=None, callback=None, prefetch_count=0):
            credentials=None
            if username is not None and password is not None:
                credentials=pika.credentials.PlainCredentials(
                        username=username,
                        password=password)

            try:
                # TODO: port should come from config
                parameters=pika.ConnectionParameters(connection_url, 5672, '/', credentials)
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

        def generate_status_file(status_file):
            modem_status_file=configparser.ConfigParser()
            if os.path.isfile(status_file):
                self.logger('Status file exist...')
                modem_status_file.read(self.status_file)

            with open(status_file, 'w') as fd_status_file:
                for name, member in Node.Category.__members__.items():
                    cat = member.value
                    if not cat in modem_status_file:
                        modem_status_file[cat]= {'COUNTER': '0'}

                modem_status_file.write(fd_status_file)

        """
        try:
            self.configreader=CustomConfigParser()
            self.config_event_rules=self.configreader.read("config/events/rules.ini")
        except CustomConfigParser.NoDefaultFile as error:
            raise(error)
        except CustomConfigParser.ConfigFileNotFound as error:
            ''' with this implementation, it stops at the first exception - intended?? '''
            raise(error)
        except CustomConfigParser.ConfigFileNotInList as error:
            raise(error)
        """
        self.m_index = m_index
        self.m_isp = m_isp
        try:
            self.logger("Attempting connection...")
            self.outgoing_connection, self.outgoing_channel = create_channel(
                    connection_url=config['NODE']['connection_url'],
                    queue_name=config['NODE']['api_id'] + '_' + config['NODE']['outgoing_queue_name'] + '_' + m_isp,
                    username=config['NODE']['api_id'],
                    password=config['NODE']['api_key'],
                    exchange_name=config['NODE']['outgoing_exchange_name'],
                    exchange_type=config['NODE']['outgoing_exchange_type'],
                    binding_key=config['NODE']['api_id'] + '_' + config['NODE']['outgoing_queue_name'] + '.' + m_isp,
                    callback=self.__sms_outgoing_callback,
                    durable=True,
                    prefetch_count=1)
            self.status_file=os.path.join( os.path.dirname(__file__), 'service_files/status', f'{Modem(self.m_index).imei}.ini')
            generate_status_file(self.status_file)
            self.logger("Connected successfully...")
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
        
    def __del__(self):
        # self.logger("calling destructor", output="stderr")
        # print("calling destructor")
        pass


    def __update_status(self, category:Category): # status file gets updated here
        self.logger(f'updating status.... {self.status_file}')
        ''' should update status file of the modem '''
        modems_status_file=configparser.ConfigParser()
        modems_status_file.read(self.status_file)

        counter=None
        with open(self.status_file, 'w') as fd_status_file:
            if category == Node.Category.FAILED:
                ''' update failed counter for modem '''
                modems_status_file[category.value]['COUNTER']=str(int(modems_status_file[category.value]['COUNTER'])+1)
                counter=int(modems_status_file[category.value]['COUNTER'])
            elif category == Node.Category.SUCCESS:
                ''' udpate success counter for modem '''
                modems_status_file[category.value]['COUNTER']=str(int(modems_status_file[category.value]['COUNTER'])+1)
                modems_status_file[Node.Category.FAILED.value]['COUNTER'] = '0'

            modems_status_file.write(fd_status_file)

        self.__event_listener(category, counter)


    def __event_listener(self, category:Category, counter):
        ''' how to test event listener without all the dep '''
        def event_run(action):
            self.logger(f'event listener taking action: {action}')

            ''' this are all external commands '''
            try:
                command = action.split(' ') + [self.m_index]
                output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('unicode_escape')
                # self.logger(output)

                return output
            except subprocess.CalledProcessError as error:
                raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)

        """
        event_rules=configparser.ConfigParser()
        event_rules.read(os.path.join(os.path.dirname(__file__), 'configs/events', f'rules.ini'))
        """
        # event_rules.read(os.path.join(os.path.dirname(__file__), 'configs/events', f'rules.ini'))

        modem_status_file=configparser.ConfigParser()
        modem_status_file.read(self.status_file)

        ''' check if the modem's status matches the event's rules '''
        status_count=int(modem_status_file[category.value]['COUNTER'])
        event_rule_count=int(self.config_event_rules[category.value]['COUNTER'])

        # print(f'status_count {status_count}')
        # print(f'event_rule_count {event_rule_count}')

        ''' -1 means do not perform this rule '''
        def format_transmissions(category, action, output):
            """
                reason_for_transmission=f"My {category.value} action was triggered!\n\n\
                        === Executing action: {category.value} =====\n
                        Results:= {output}"
            """
            return (f"My *{category}* action was triggered!\n\n"
            f"=== *Executing action:* _{action}_ =====\n\n"
            f"*Results:=* {output}")

        def next_transmission():
            self.logger('updating next transmission...')
            modems_status_file=configparser.ConfigParser()
            modems_status_file.read(self.status_file)

            with open(self.status_file, 'w') as fd_modems_status_file:
                modems_status_file['TRANSMISSION']['counter'] = str(
                        float(time.time() + (float(self.config['TRANSMISSION']['duration'])*60)))
                modems_status_file.write(fd_modems_status_file)

        if event_rule_count > -1 and status_count >= event_rule_count:
            try:
                modems_status_file=configparser.ConfigParser()
                modems_status_file.read(self.status_file)

                next_transmission_timer = float(modems_status_file['TRANSMISSION']['counter'])
                request_transmission_timer = time.time()
                ''' add some layer which transmits the feedback of the event listener to something else '''
                ''' some DekuFeedbackLayer, can then be abstracted for Telegram or other platforms '''
                ''' #TODO: increment throught he various actions based on trailing # '''
                i=1
                action = self.config_event_rules[category.value]['ACTION']
                output=event_run(action)
                if transmission_layer is not None and request_transmission_timer > next_transmission_timer:
                    transmission_layer.send(format_transmissions(category.value, action, output))
                print(output)

                ''' check transmission state '''

                while( ('ACTION'+str(i)) in self.config_event_rules[category.value]):
                    # action = self.config_event_rules[category.value]['ACTION'+str(i)]
                    output=event_run(self.config_event_rules[category.value]['ACTION'+str(i)])

                    ''' choose from a list of numbers to receive the notifications '''
                    ''' choose from a list of protocols which ones receive the notifications '''
                    print(output)
                    if transmission_layer is not None and request_transmission_timer > next_transmission_timer:
                        transmission_layer.send(format_transmissions(category.value, action, output))

                    i+=1

                if request_transmission_timer > next_transmission_timer:
                    next_transmission()
            except subprocess.CalledProcessError as error:
                # print(error)
                ''' in this case don't reset the counter - so it tries again '''
                # log_trace(f"Event listener output: {error.output.decode('utf-8')}")
                print(error.output)
            except Exception as error:
                log_trace(traceback.format_exc())
            """
            else:
                ''' in this case, reset the counter '''
            """

    def __sms_outgoing_callback(self, ch, method, properties, body):
        # TODO: verify data coming in is actually a json
        json_body = json.loads(body.decode('unicode_escape'))
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
            # number_isp False says do not base on the number's isp
            Deku.send(text=text, number=number, m_index=self.m_index, number_isp=False)

        except Deku.InvalidNumber as error:
            ''' wrong number: message does not comes back '''
            self.logger(f'{error.message} - {error.number}')
            log_trace(error.message)
            self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
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

            ch.basic_reject(
                    delivery_tag=method.delivery_tag, 
                    requeue=True)
            self.outgoing_connection.sleep(5)

        except subprocess.CalledProcessError as error:
            ''' generic system error: message comes back '''
            ''' requires further processing '''
            self.logger('sending sms failed...', output='stderr')
            # self.logger(error.output, ot)
            # self.logger(error.stdout)
            if self.previousError != error.output:
                log_trace(error.output.decode('utf-8'))
                self.logger(error.output.decode('utf-8'))

            self.previousError = error.output.decode('utf-8')
            ch.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
            '''node keeps track of this failures, and send message to 
            server after a benchmark failed limit
            '''
            '''
            options here---
            -> open up connection and remotely send USSD request - manual intervention
            -> 
            # with open(os.path.join(os.path.dirname(__file__), 'locks', f'{Modem(m_index).imei}.ini'), 'w') as log_file:
            '''
            self.__update_status(Node.Category.FAILED)
            # self.__event_watch(category)


        except Exception as error:
            ''' code crashed here '''
            self.logger('sending sms failed...', output='stderr')
            log_trace(traceback.format_exc())
            ch.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
        else:
            ''' message ack happens here '''
            ''' after successful delivery, pause for a bit before continuing '''
            # self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger('message sent successfully')

            ''' 0 = success '''
            self.__update_status(Node.Category.SUCCESS)
            # self.__event_watch(category)

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
        wd = threading.Thread(target=self.__watchdog_monitor, daemon=True)
        wd.start()

        self.logger('outgoing: waiting for message...')
        try:
            ''' messages to be sent via SMS '''
            self.logger('outgoing consumption starting...')
            self.outgoing_channel.start_consuming() #blocking
            wd.join()
        except pika.exceptions.AMQPHeartbeatTimeout as error:
            ''' internet issues and might have disconnected '''

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
            if self.m_index in l_threads:
                del l_threads[self.m_index]
        # self.logger('ending consumption....')

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

    ''' instantiate configuration for all of Deku '''
    try:
        Deku()
        configreader=CustomConfigParser()
        config_event_rules=configreader.read("configs/events/rules.ini")
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
                        outgoing_node=Node(m_index, m_isp, config, config_event_rules)
                        # print(outgoing_node, outgoing_node.__dict__)
                        outgoing_thread=threading.Thread(target=outgoing_node.start_consuming, daemon=True)

                        # l_threads[m_index] = [outgoing_thread, routing_thread]
                        l_threads[m_index] = [outgoing_thread]
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
    global transmission_layer
    transmission_layer=None
    try:
        transmission_layer = TransmissionLayer()
        config=None
        config=CustomConfigParser()
        config=config.read("configs/config.ini")

        print('* master watchdog booting up')
        master_watchdog(config)
    except CustomConfigParser.NoDefaultFile as error:
        print(traceback.format_exc())
    except CustomConfigParser.ConfigFileNotFound as error:
        ''' with this implementation, it stops at the first exception - intended?? '''
        print(traceback.format_exc())
    except CustomConfigParser.ConfigFileNotInList as error:
        print(traceback.format_exc())
