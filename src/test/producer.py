#!/usr/bin/env python3

import pika
import sys, os
import json
import configparser

if __name__ == "__main__":
    """
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(os.path.join(os.path.dirname(__file__), '../configs', 'config.ini'))

    username=config['NODE']['api_id']
    password=config['NODE']['api_key']
    """
    credentials=pika.credentials.PlainCredentials(
            username='guest',
            password='guest')

    connection_url='localhost'
    parameters=pika.ConnectionParameters(connection_url, 5672, '/', credentials)
    connection=pika.BlockingConnection(parameters=parameters)

    channel = connection.channel()

    routing_key='inbound.route.route'
    number = sys.argv[1]

    message = ' '.join(sys.argv[2:]) or "Hello World!"
    data = json.dumps({"text":message, "MSISDN":number})

    channel.basic_publish( 
            exchange='',
            routing_key=routing_key,
            body=data,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
    )
    # print(" [x] Sent %r" % message)
    print(f"[x] message; {message} ::\n\tsent to {number}")
    connection.close()

