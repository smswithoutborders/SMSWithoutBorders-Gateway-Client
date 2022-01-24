#!/usr/bin/env python3

import pika
class RabbitMQBroker:

    @staticmethod
    def create_channel(connection_url, queue_name, exchange_name=None, 
            exchange_type=None, durable=False, binding_key=None, callback=None, 
            prefetch_count=0, connection_port=5672, heartbeat=600, 
            blocked_connection_timeout=None, username='guest', password='guest', retry_delay=10):

        credentials=pika.PlainCredentials(username, password)
        try:
            parameters=pika.ConnectionParameters(
                    connection_url, 
                    connection_port, 
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
            raise error


