#!/usr/bin/env python3

class GatewayIncoming:
    def __init__(self, modem_index, modem_isp, config, 
            config_isp_default, config_isp_operators, ssl=None):

        self.modem_index = modem_index
        self.modem_isp = modem_isp
        self.config = config

        formatter = logging.Formatter(
                '%(asctime)s|[%(levelname)s][%(module)s] [%(name)s] %(message)s', 
                datefmt='%Y-%m-%d %H:%M:%S')

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger_name=f"{self.modem_isp}:{self.modem_index}"
        self.logging=logging.getLogger(logger_name)
        self.logging.setLevel(logging.NOTSET)
        self.logging.addHandler(handler)

        '''
        log_file_path = os.path.join(os.path.dirname(__file__), 'services/logs', 'service.log')
        handler = logging.FileHandler(log_file_path)
        '''
        handler.setFormatter(formatter)
        self.logging.addHandler(handler)

        self.logging.propagate = True
        self.sleep_time = int(self.config['MODEMS']['sleep_time'])

    def __publish__(self, sms, queue_name):
        try:
            self.publish_channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps({"text":sms.text, "phonenumber":sms.number}),
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            self.logging.info("published %s",{"text":sms.text, "phonenumber":sms.number})
        except Exception as error:
            raise error

    def __exec_remote_control__(self, sms):
        try:
            self.logging.debug("Checking for remote control [%s] - [%s]", 
                    sms.text, sms.number)
            if RemoteControl.is_executable(text=sms.text):
                self.logging.info("Valid remote control activated [%s]", 
                        sms.text)
                if RemoteControl.is_whitelist(number=sms.number):
                    output = RemoteControl.execute(text=sms.text)
                    self.logging.debug(output)
                else:
                    self.logging.warning(
                            "Remote Control requester not whitelisted - [%s]",
                            sms.number)
            else:
                self.logging.debug("Not valid remote control command")
        except Exception as error:
            raise error


    def monitor_incoming(self):
        connection_url=self.config['GATEWAY']['connection_url']
        queue_name=self.config['GATEWAY']['routing_queue_name']

        # self.logging.info("incoming %s", self.modem_index)
        try:
            while Deku.modem_ready(self.modem_index, index_only=True):
                if not hasattr(self, 'publish_connection') or \
                        self.publish_connection.is_closed:
                    self.publish_connection, self.publish_channel = create_channel(
                            connection_url=connection_url,
                            queue_name=queue_name,
                            heartbeat=600,
                            blocked_connection_timeout=60,
                            durable=True)

                messages=Modem(self.modem_index).SMS.list('received')
                # self.logging.debug(messages)
                for msg_index in messages:
                    sms=Modem.SMS(index=msg_index)

                    try:
                        self.__publish__(sms=sms, queue_name=queue_name)
                    except Exception as error:
                        self.logging.critical(error)

                    else:
                        try:
                            Modem(self.modem_index).SMS.delete(msg_index)
                        except Exception as error:
                            self.logging.error(traceback.format_exc())
                        else:
                            try:
                                self.__exec_remote_control__(sms)
                            except Exception as error:
                                self.logging.exception(traceback.format_exc())

                messages=[]
                time.sleep(self.sleep_time)

        except Modem.MissingModem as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
        except Modem.MissingIndex as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
            self.logging.warning("Modem [%s] Index not initialized", self.modem_index)
        except Exception as error:
            self.logging.exception(traceback.format_exc())
            self.logging.warning("Modem [%s] not initialized", self.modem_index)
            self.logging.critical(traceback.format_exc())
        finally:
            # self.logging.info(">> sleep time %s", self.sleep_time)
            time.sleep(self.sleep_time)

        # self.logging.warning("disconnected") 
        try:
            if self.modem_index in active_threads:
                del active_threads[self.modem_index]
        except Exception as error:
            raise error

    def __del__(self):
        if self.publish_connection.is_open:
            self.publish_connection.close()
        self.logging.debug("cleaned up gateway instance")
