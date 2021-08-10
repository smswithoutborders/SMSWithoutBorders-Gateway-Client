#!/usr/bin/python3

''' testing criterias----
- when modem is present a node should start up
    - should be able to receive messages from a producer
'''

import sys, os, threading
import asyncio, configparser

import pika

sys.path.append(os.path.abspath(os.getcwd()))
from mmcli_python.modem import Modem

class Node:
    def __init__(self, m_index, queue_name='', exchange_type='direct'):
        ''' bringing config in here means it's hot reloaded when nodes are created '''
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), '', 'config.ini'))

        ''' 
        queue_name : should be name of isp - no cus this would delete the entirty when 
        closed
        '''

        self.exchange=config['NODE']['exchange']
        self.m_index=m_index
        self.queue_name=queue_name
        self.exchange_type=exchange_type
        connection_url = config['NODE']['connection_url']

        connection=pika.BlockingConnection(pika.ConnectionParameters(connection_url))
        self.channel=connection.channel()

        ''' listening exchange creation on the stack '''
        self.channel.exchange_declare(exchange=self.exchange, exchange_type=self.exchange_type)

        ''' listening queue creation on the stack'''
        # result=channel.queue_declare(queue=queue_name, exclusive=True)
        self.channel.queue_declare(queue=self.queue_name)

        ''' bind queue to exchange '''
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name)

        ''' consumer properties '''
        ''' no auto_ack '''

        # TODO: delete this, ack should be manual
        self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.__callback, auto_ack=True)

        '''
        self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.__callback)
        '''

        ''' set fair dispatch '''
        self.channel.basic_qos(prefetch_count=int(config['NODE']['prefetch_count']))

    def __callback(self, ch, method, properties, body):
        print(f'\t*[{self.m_index}] message: {body}')

    def start_consuming(self):
        print(f'\t[{self.m_index}]* waiting for message...')
        self.channel.start_consuming()

def main():
    ''' - when modem open worker
        - when no worker close worker
    '''
    def available_modem():
        return Modem.list()

    # indexes=available_modem()
    indexes=['1', '2']
    print('* starting consumer for modems with indexes:', indexes)

    l_threads=[]
    for m_index in indexes:
        # isp_name=Tools.ISP.modem('cameroon', '')
        isp_name="MTN1"
        print('\t* starting consumer for:', m_index, isp_name)

        node=Node(m_index, isp_name)
        thread=threading.Thread(target=node.start_consuming, daemon=True)
        l_threads.append(thread)

    for thread in l_threads:
        thread.start()

    for thread in l_threads:
        thread.join()

if __name__ == "__main__":
   main()

