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
from configparser import ConfigParser, ExtendedInterpolation

import pika

sys.path.append(os.path.abspath(os.getcwd()))
from mmcli_python.modem import Modem


connection=None
config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), '', 'config.ini'))

class Node:
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

        self.exchange=config['NODE']['exchange_name']
        self.queue_name=config['NODE']['queue_name']
        self.binding_key=f"{config['NODE']['binding_key']}.{m_isp}"
        self.channel=connection.channel()

        ''' bind queue to exchange '''
        try:

            print(f'\t* [{self.m_index}] binding key: {self.binding_key}')
            self.channel.queue_bind(
                    exchange=self.exchange, 
                    queue=self.queue_name, 
                    routing_key=self.binding_key)

        except pika.exceptions.ChannelClosedByBroker as error:
            print(error)
            sys.exit(1)
        except Exception as error:
            print(traceback.format_exc())
            sys.exit(1)

        ''' consumer properties '''
        ''' no auto_ack '''

        # TODO: delete this, ack should be manual
        self.channel.basic_consume(
                queue=self.queue_name, 
                on_message_callback=self.__callback, 
                auto_ack=bool(int(config['NODE']['auto_ack'])))

        '''
        self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.__callback)
        '''

        ''' set fair dispatch '''
        self.channel.basic_qos(prefetch_count=int(config['NODE']['prefetch_count']))

    def __callback(self, ch, method, properties, body):
        print(f'\t* [{self.m_index}] message: {body}')

    def start_consuming(self):
        print(f'\t* [{self.m_index}] waiting for message...')
        self.channel.start_consuming()

def main():
    l_threads=[]
    # indexes=available_modem()
    indexes=['1', '2']
    print('* starting consumer for modems with indexes:', indexes)

    for m_index in indexes:
        # isp_name=Tools.ISP.modem('cameroon', '')
        m_isp="mtn"

        print('\t* starting consumer for:', m_index, m_isp)
        node=Node(m_index, m_isp)

        thread=threading.Thread(target=node.start_consuming, daemon=True)
        l_threads.append(thread)

    for thread in l_threads:
        thread.start()

    for thread in l_threads:
        thread.join()

if __name__ == "__main__":
    main()

