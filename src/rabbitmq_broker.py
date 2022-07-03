#!/usr/bin/env python3

import pika
import logging

class RabbitMQBroker:

    @staticmethod
    def on_close_callback(**kwargs) -> None:
        """Call in case Pika connection is closed.
        """
        logging.info("PIKA CONNECTION CLOSED")

    @staticmethod
    def create_channel(
            connection_url, 
            queue_name, 
            exchange_name=None, 
            exchange_type='topic', 
            connection_name='sample_connection_name',
            durable=True, 
            binding_key=None, 
            callback=None, 
            prefetch_count=1, 
            connection_port=5672, 
            heartbeat=10, 
            blocked_connection_timeout=None, 
            username='guest', 
            password='guest') -> None:

        credentials=pika.PlainCredentials(username, password)
        try:
            client_properties = {'connection_name' : connection_name}

            parameters=pika.ConnectionParameters(
                    connection_url, 
                    connection_port, 
                    '/',
                    credentials,
                    heartbeat=heartbeat,
                    client_properties=client_properties
                    )

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

        except pika.exceptions.AMQPConnectionError as error:
            raise error

        except Exception as error:
            raise error

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


