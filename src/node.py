#!/usr/bin/env python3

import os
import sys
import threading
import traceback
import socket
import subprocess
import json
import time
import pika 
import configparser
import logging

from colorama import init
from datetime import datetime
from enum import Enum

# sys.path.append(os.path.abspath(os.getcwd()))
from deku import Deku
from mmcli_python.modem import Modem
from transmissionLayer import TransmissionLayer
from common.CustomConfigParser.customconfigparser import CustomConfigParser

'''
resources:
    - https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html?highlight=BlockingChannel#pika.adapters.blocking_connection.BlockingChannel
'''

class Node:
    modem_index = None
    modem_isp = None
    config = None

    outgoing_connection=None
    outgoing_channel=None

    previousError=None


    class Category(Enum):
        SUCCESS='SUCCESS'
        FAILED='FAILED'
        UNKNOWN='UNKNOWN'
        TRANSMISSION='TRANSMISSION'


    @staticmethod
    def create_channel(connection_url, queue_name, username=None, 
            password=None, exchange_name=None, exchange_type=None, durable=False, 
            binding_key=None, callback=None, prefetch_count=0, retry_delay=10):

        credentials=None
        if username is not None and password is not None:
            credentials=pika.credentials.PlainCredentials(
                    username=username,
                    password=password)

        try:
            # TODO: port should come from config
            parameters=pika.ConnectionParameters(
                    connection_url, 
                    5672, 
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
            raise(error)
        '''
        except pika.exceptions.ConnectionClosedByBroker as error:
            raise(error)
        except pika.exceptions.AMQPChannelError as error:
            raise(error)
        except pika.exceptions.AMQPConnectionError as error:
            raise(error)
        except socket.gaierror as error:
            raise(error)
        '''

    def generate_status_file(self, status_file):
        modem_status_file=configparser.ConfigParser()
        if os.path.isfile(status_file):
            logging.info('Status file exist...')
            modem_status_file.read(self.status_file)

        with open(status_file, 'w') as fd_status_file:
            for name, member in Node.Category.__members__.items():
                cat = member.value
                if not cat in modem_status_file:
                    modem_status_file[cat]= {'COUNTER': '0'}

            modem_status_file.write(fd_status_file)

    def __init__(self, modem_index, modem_isp, config, config_event_rules, deku):
        self.deku = deku
        self.config_event_rules = config_event_rules
        self.config = config
        self.modem_index = modem_index
        self.modem_isp = modem_isp

        self.modem = Modem(self.modem_index)

        self.connection_url=config['NODE']['connection_url']
        self.queue_name=(
            config['NODE']['api_id'] 
            + '_' + config['NODE']['outgoing_queue_name'] 
            + '_' + modem_isp)
        self.username=config['NODE']['api_id']
        self.password=config['NODE']['api_key']
        self.exchange_name=config['NODE']['outgoing_exchange_name']
        self.exchange_type=config['NODE']['outgoing_exchange_type']
        self.binding_key=(
            config['NODE']['api_id'] 
            + '_' + config['NODE']['outgoing_queue_name'] 
            + '.' + modem_isp)
        self.callback=self.__callback
        self.durable=True
        self.prefetch_count=1

        self.sleep_time = int(config['MODEMS']['sleep_time']) if \
                int(config['MODEMS']['sleep_time']) > 3 else 3

        formatter = logging.Formatter('%(asctime)s|[%(levelname)s][%(module)s] [%(name)s] %(message)s', 
                datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger_name=f"{self.modem_isp}:{self.modem_index}"
        self.logging=logging.getLogger(logger_name)
        self.logging.setLevel(logging.NOTSET)
        self.logging.addHandler(handler)

        handler = logging.FileHandler('src/services/logs/service.log')
        handler.setFormatter(formatter)
        self.logging.addHandler(handler)

        self.logging.propagate = False

    def status(self):
        waiting_message_count = self.outgoing_channel.get_waiting_message_count()
        return waiting_message_count

    def create_connection(self):
        self.logging.info("starting connection")
        try:
            self.outgoing_connection, self.outgoing_channel = Node.create_channel(
                    connection_url=self.connection_url,
                    queue_name=self.queue_name,
                    username=self.username,
                    password=self.password,
                    exchange_name=self.exchange_name,
                    exchange_type=self.exchange_type,
                    binding_key=self.binding_key,
                    callback=self.callback,
                    durable=self.durable,
                    prefetch_count=self.prefetch_count)
        except Exception as error:
            raise(error)
        
    def update_status(self, category:Category): # status file gets updated here
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

        self.event_listener(category, counter)

    def event_run(self, action):
        try:
            command = action.split(' ') + [self.modem_index]
            output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('unicode_escape')

            return output
        except subprocess.CalledProcessError as error:
            raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)


    def next_transmission(self):
        modems_status_file=configparser.ConfigParser()
        modems_status_file.read(self.status_file)

        time_now = float(time.time())
        transmission_duration_secs = float(self.config['TRANSMISSION']['duration'])*60

        with open(self.status_file, 'w') as fd_modems_status_file:
            modems_status_file['TRANSMISSION']['counter'] = str(
                    time_now + transmission_duration_secs)

            modems_status_file.write(fd_modems_status_file)
        self.logging.info("updated duration for transmissions")

    def can_transmit(self, modems_status_file):
        next_transmission_timer = float(modems_status_file['TRANSMISSION']['counter'])
        request_transmission_timer = time.time()

        return \
                transmission_layer is not None and \
                request_transmission_timer > next_transmission_timer

    def event_listener(self, category:Category, counter):
        modem_status_file=configparser.ConfigParser()
        modem_status_file.read(self.status_file)

        ''' check if the modem's status matches the event's rules '''
        status_count=int(modem_status_file[category.value]['COUNTER'])
        event_rule_count=int(self.config_event_rules[category.value]['COUNTER'])

        if event_rule_count > -1 and status_count >= event_rule_count:
            try:
                modems_status_file=configparser.ConfigParser()
                modems_status_file.read(self.status_file)

                action = self.config_event_rules[category.value]['ACTION']
                output = self.event_run(action)
                self.logging.info(output)

                if self.can_transmit(modems_status_file):
                    transmission_layer.send(format_transmissions(category.value, action, output))

                i=1
                while ('ACTION'+str(i)) in self.config_event_rules[category.value]:
                    output= self.event_run(self.config_event_rules[category.value]['ACTION'+str(i)])
                    self.logging.info(output)
                    if transmission_layer is not None and \
                            request_transmission_timer > next_transmission_timer:
                        transmission_layer.send(format_transmissions(category.value, action, output))

                    i+=1

                if request_transmission_timer > next_transmission_timer:
                    self.next_transmission()
            except subprocess.CalledProcessError as error:
                raise(error)
            except Exception as error:
                raise(error)


    def __callback(self, ch, method, properties, body):
        # TODO: verify data coming in is actually a json
        json_body = json.loads(body.decode('unicode_escape'))
        self.logging.debug(json_body)

        if not "text" in json_body:
            self.logging.warning('poorly formed message - text missing')
            return 
        
        if not "number" in json_body:
            self.logging.warning('poorly formed message - number missing')
            return 

        text=json_body['text']
        number=json_body['number']

        try:
            self.logging.info('sending sms')
            deku.send( text=text, number=number, modem_index=self.modem_index, 
                    number_isp=False)
            self.logging.info('sms sent')
        except Deku.InvalidNumber as error:
            self.logging.warning("invalid number, dumping message")
            self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
        except Deku.NoAvailableModem as error:
            self.logging.warning("no available modem while trying to send")
            ch.basic_reject(
                    delivery_tag=method.delivery_tag, 
                    requeue=True)
            self.outgoing_connection.sleep(self.sleep_time)

        except subprocess.CalledProcessError as error:
            if ch.is_open:
                ch.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
            try:
                self.update_status(Node.Category.FAILED)
            except Exception as error:
                self.logging.error(traceback.format_exc())

        except Exception as error:
            if ch.is_open:
                ch.basic_reject( delivery_tag=method.delivery_tag, requeue=True)
            self.logging.exception(error)
        else:
            if ch.is_open:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            try:
                self.update_status(Node.Category.SUCCESS)
            except Exception as error:
                self.logging.exception(traceback.format_exc())
            self.logging.info("sms sent successfully")
        finally:
            if ch.is_closed:
                return

    def __modem_monitor(self):
        self.logging.debug("monitoring state of modem")
        try:
            messages = self.modem.SMS.list('received')
            while deku.modem_ready(self.modem_index):
                time.sleep(self.sleep_time)
            self.logging.warning("disconnected")
        except Exception as error:
            raise(error)
        finally:
            try:
                self.outgoing_connection.close(reply_code=1, reply_text='modem no longer available')
            except Exception as error:
                # raise(error)
                ''' seems like will always raise and exception '''
                pass
            finally:
                if self.modem_index in active_nodes:
                    del active_nodes[self.modem_index]

    def start_consuming(self):
        self.logging.debug("incoming consumer started")
        self.logging.info("# waiting messages %d", self.status())

        self.status_file=os.path.join( 
                os.path.dirname(__file__), 
                'services/status', f'{self.modem.imei}.ini')

        self.generate_status_file(self.status_file)
        wd = threading.Thread(target=self.__modem_monitor, daemon=True)
        wd.start()

        try:
            self.outgoing_channel.start_consuming() #blocking
            wd.join()

        except Exception as error:
            raise(error)
        finally:
            if self.modem_index in active_nodes:
                del active_nodes[self.modem_index]


'''++ startup routines'''
def init_nodes(indexes, config, config_isp_default, config_isp_operators, config_event_rules):
    logging.debug("initializing nodes")
    isp_country = config['ISP']['country']
    for modem_index in indexes:
        if modem_index not in active_nodes:
            if not deku.modem_ready(modem_index):
                logging.debug("modem(%s) not ready", mdoem_index)
                continue
            try:
                modem_isp = deku.ISP.modems(
                        operator_code=Modem(modem_index).operator_code, 
                        country=isp_country)

                node=Node(modem_index, modem_isp, config, config_event_rules, deku=deku)
                node_thread=threading.Thread(
                        target=node.start_consuming, daemon=True)

                active_nodes[modem_index] = [node_thread, node]

            except Exception as error:
                raise(error)

def start_nodes():
    for modem_index, thread_n_node in active_nodes.items():
        thread = thread_n_node[0]
        node = thread_n_node[1]
        try:
            if thread.native_id is None:
                logging.debug("starting nodes")
                node.create_connection()
                thread.start()

        except socket.gaierror as error:
            logging.warning("unable to resolve server location (check internet connection)")
        except pika.exceptions.AMQPConnectionError as error:
            logging.warning("unable to talk to server location (check internet connection)")
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
            indexes, locked_indexes = deku.modems_ready(remove_lock=True)

            stdout_logging.info("available modems %d [%s], locked modems %d [%s]", 
                    len(indexes), indexes, len(locked_indexes), locked_indexes)

            if len(indexes) < 1:
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

def initiate_transmissions():
    logging.debug("instantiating transmissions")
    global transmission_layer
    transmission_layer=None

    try:
        transmission_layer = TransmissionLayer()
    except CustomConfigParser.NoDefaultFile as error:
        raise(error)
    except CustomConfigParser.ConfigFileNotFound as error:
        raise(error)
    except CustomConfigParser.ConfigFileNotInList as error:
        raise(error)
    except Exception as error:
        raise(error)

def format_transmissions(category, action, output):
    msg=f"Category: {category}\nAction: {action}\nOutput: {output}" 
    return msg

def main(config, config_event_rules, config_isp_default, config_isp_operators):
    logging.debug("node main started")
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

    try:
        initiate_transmissions()
        manage_modems(config=config, 
                config_event_rules=config_event_rules,
                config_isp_default=config_isp_default,
                config_isp_operators=config_isp_operators)

    except Exception as error:
        logging.exception(error)
    """
    except CustomConfigParser.NoDefaultFile as error:
        logging.error(traceback.format_exc())
    except CustomConfigParser.ConfigFileNotFound as error:
        ''' with this implementation, it stops at the first exception - intended?? '''
        logging.error(traceback.format_exc())
    except CustomConfigParser.ConfigFileNotInList as error:
        logging.error(traceback.format_exc())
    """

if __name__ == "__main__":
    main()
