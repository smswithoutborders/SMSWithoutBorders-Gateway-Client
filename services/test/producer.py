#!/usr/bin/env python3

import pika
import sys, os
import json
import configparser

if __name__ == "__main__":
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(os.path.join(os.path.dirname(__file__), '../configs', 'config.ini'))

    username=config['NODE']['api_id']
    password=config['NODE']['api_key']
    credentials=pika.credentials.PlainCredentials(
            username=username,
            password=password)

    # TODO: port should come from config
    connection_url=config['NODE']['connection_url']
    parameters=pika.ConnectionParameters(connection_url, 5672, '/', credentials)
    connection=pika.BlockingConnection(parameters=parameters)

    '''
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config['NODE']['connection_url']))
    '''

    channel = connection.channel()

    # queue_name = config_queue_name + _ + isp
    '''
    queue_name = config['NODE']['outgoing_queue_name'] + '_' + sys.argv[1].lower()
    routing_key = config['NODE']['outgoing_queue_name'] + '.' + sys.argv[1]
    '''
    queue_name=config['NODE']['api_id'] + '_' + config['NODE']['outgoing_queue_name'] + '_' + sys.argv[1].lower()
    routing_key=config['NODE']['api_id'] + '_' + config['NODE']['outgoing_queue_name'] + '.' + sys.argv[1].lower()
    
    ''' creates the exchange '''
<<<<<<< HEAD
    """
=======
    '''
>>>>>>> aad65cc86d93d6cd68bd2905abd88f0b983afd28
    channel.exchange_declare( 
            exchange=config['NODE']['outgoing_exchange_name'], exchange_type=config['NODE']['outgoing_exchange_type'])
    '''

    """
    number = sys.argv[2]
    message = ' '.join(sys.argv[3:]) or "Hello World!"
    data = json.dumps({"text":message, "number":number})

    channel.basic_publish(
        exchange=config['NODE']['outgoing_exchange_name'],
        # routing_key=queue_name.replace('_', '.'),
        routing_key=routing_key,
        body=data,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    # print(" [x] Sent %r" % message)
    print(f"[x] message; {message} ::\n\tsent to {number}")
    connection.close()

