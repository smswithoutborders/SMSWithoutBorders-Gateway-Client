#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import os, sys, time, queue, json, traceback
import configparser, threading
from datetime import datetime
import subprocess

sys.path.append(os.path.abspath(os.getcwd()))
from mmcli_python.modem import Modem

class Deku(Modem):

    class InvalidNumber(Exception):
        def __init__(self, number, message):
            self.number=number
            self.message=message
            super().__init__(self.message)

    class NoAvailableModem(Exception):
        def __init__(self, message):
            self.message=message
            super().__init__(self.message)

    class ISP():
        '''
        purpose: helps get the service provider for a number
        - checks the isp_configs for matching rules
        - numbers have to be in the E.164 standards (country code included); https://en.wikipedia.org/wiki/E.164
        '''

        @staticmethod
        def determine(number, country, parsed_rules=None):
            import configparser, re
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'configs/isp', 'default.ini'))

            if number.find(config['country_codes'][country]) > -1:
                number= number.replace(config['country_codes'][country], '')
            # print('number', number)
            for rules in config[country]:
                # print(rules)
                ''' checks if has country code '''
                for rule in config[country][rules].split(','):
                    if re.search(rule, number):
                        return rules

            print('could not determine rule')
            return None

        @staticmethod
        def modems(country, operator_code):
            # print(f"determining modem's isp {country} {operator_code}")
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'configs/isp', 'operators.ini'))

            for isp in config[country]:
                if config[country][isp].lower() == operator_code.lower():
                    # print('modems isp found: ', isp)
                    return isp

            return None

        
    @staticmethod
    def modem_locked(identifier, id_type:Modem.IDENTIFIERS=Modem.IDENTIFIERS.IMEI, benchmark_remove=True):
        '''
        pdu-type might be what determines the kind of message this is
        - check latest message, if pdu-type == submit
        - outbound = send
        - inbound = deliver


        latest message would determine if modem is available or not
        '''
        if id_type == Modem.IDENTIFIERS.INDEX:
            ''' convert to imei '''
            identifier= Modem(identifier).imei

        lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{identifier}.lock')
        lock_type=None
        start_time=None
        if os.path.isfile(lock_dir):
            '''
            print(f'{identifier}.lock exist')
            # return True
            # checks state of modems last messages
            all_messages = Modem.SMS.list(k=False)
            # print(all_messages)
            for messages in all_messages:
                # 0 = index, 1 = (type)
                if messages[1].find('unknown') > -1:
                    # figure shit out
            '''

            ''' checks the duration of the lock, then frees up the lock file '''
            lock_config = configparser.ConfigParser()
            lock_config.read(lock_dir)
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))

            start_time = float(lock_config['LOCKS']['START_TIME'])
            lock_type = lock_config['LOCKS']['TYPE']

            ''' benchmark limit should come from configs 
            calculate the time difference
            '''
            ''' how long should benchmarks last before expiring '''
            benchmark_timelimit = int(config['MODEMS']['failed_sleep'])

            ''' how long should benchmarks last before expiring if state is busy '''
            busy_timelimit = int(config['MODEMS']['busy_benchmark_limit'])

            # print(f'lt: {lock_type}\nnow: {time.time()}\nstart_time: {start_time}\ndiff: {time.time() - start_time}')
            if benchmark_remove and ((time.time() - start_time ) > benchmark_timelimit and lock_type == 'BENCHMARK') or ((time.time() - start_time ) > busy_timelimit and lock_type == 'BUSY'): #seconds
                # print('\ttype = benchmark')
                ''' set the file free '''
                os.remove(lock_dir)
                 #print('set lock file free')
                return False, lock_type, lock_dir
            # print('\ttype = busy')
            return True, lock_type, lock_dir
            
        # print(f'{identifier} no lock file')
        return False, lock_type, lock_dir
    
    @staticmethod
    def modem_ready(modem_index):
        # indexes=Modem.list()
        
        ''' check every criteria
        - network coverage
        - available isp
        -etc
        '''
        try:
            moc = Modem(modem_index).operator_code
        except NameError as error:
            # raise Exception(error)
            return False
        except Exception as error:
            raise Exception(error)

        # print('moc:', moc)
        return modem_index in Modem.list() and moc != '--' and moc is not None

    @staticmethod
    def modems_ready(isp=None, country=None, remove_lock=False):
        available_indexes=[]
        indexes= Modem.list()
        # print('fetching available modems')

        for m_index in indexes:
            # filter for same isp
            '''
            checking operator_name is wrong... the name changes very frequently
            use operator code instead
            '''
            # print(f'Modem operator code {Modem(m_index).operator_code}')
            # print(Deku.ISP.__dict__)
            # print(country)

            ''' should be in setting before deciding to use isp checking here -
            credit is still a viable option '''
            if isp is None:
                ''' when sending, modem can't take another job unless faulty node 
                if not Deku.modem_locked(identifier=index, id_type=Modem.IDENTIFIERS.INDEX)[0]:
                    # print('modem is not locked')
                    available_indexes.append(index)
                '''
                if Deku.modem_ready(m_index):
                    available_indexes.append(m_index)

            else:
                if country is None:
                    raise Exception('country cannot be None')

                modem_isp = Deku.ISP.modems(operator_code=Modem(m_index).operator_code, country=country)
                status, lock_type, lock_file =Deku.modem_locked(Modem(m_index).imei)
                print('lock status', status)
                if isp == modem_isp and not status:
                    available_indexes.append(m_index)
        return available_indexes


    @staticmethod
    # def send(text, number, timeout=20, q_exception:queue=None, identifier=None, t_lock:threading.Lock=None):
    def send(text, number, timeout=20, q_exception:queue=None, identifier=None, lock:threading.Lock=None):
        '''
        options to help with load balancing:
        - based on the frequency of single messages coming in, can choose to create locks modem

        Questions:
        - how can modem give up trying to send out a message and let another modem take a short
        - answer: by locking itself for a longer time period and letting the other modems have access
        aka (lock on fail - aka benchmark limit) - giving a shot with 1 min

        sample lock file:
        lock_start_time = (epoch time)
        lock_type = [benchmark_limit, busy, break]

            benchmark_limit = failed too many times
            
            busy = currently has a job

            break = has done too many single task, trying to switch up other modems
        '''
        print(f'new deku send request {text}, {number}')
        if text is None:
            raise Exception('text cannot be empty')
        if number is None:
            raise Exception('number cannot be empty')

        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
        country = config['ISP']['country']
        print(f'number {number}, country {country}')
        isp=Deku.ISP.determine(number=number, country=country)

        if isp is None:
            '''invalid number, should completely delete this from queueu'''
            raise Deku.InvalidNumber(number, 'invalid number')

        # print('isp ', isp)
        # threading.Thread.acquire(blocking)
        index= Deku.modems_ready(isp=isp, country=country)
        print('ready index:', index)

        # print('available modem with index at', index)
        lock_dir=None

        if len(index) < 1 or index is None:
            msg=f'message[{identifier}] - no available modem for type {isp}'

            ''' release thread lock '''
            if lock is not None and lock.locked():
                lock.release()
                print('\tthread lock released')

            if q_exception is not None:
                q_exception.put(Exception(json.dumps({"msg":msg, "_id":identifier})))
                return 1

            else:
                # raise Exception(msg)
                raise Deku.NoAvailableModem(msg)


        modem = Modem(index[0])
        lock_dir = None
        lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{modem.imei}.lock')
        def create_benchmark_file():
            with open(lock_dir, 'w') as lock_file:
                write_config = configparser.ConfigParser()
                write_config['LOCKS'] = {}
                write_config['LOCKS']['TYPE'] = 'BENCHMARK'
                write_config['LOCKS']['START_TIME'] = str(time.time())
                write_config.write(lock_file)

        try:
            if os.path.isfile(lock_dir):
                ''' removing lock file cus if here, benchmark should 
                have been checked already
                '''
                os.remove(lock_dir)

            with open(lock_dir, 'w') as lock_file:
                write_config = configparser.ConfigParser()
                write_config['LOCKS'] = {}
                write_config['LOCKS']['TYPE'] = 'BUSY'
                write_config['LOCKS']['START_TIME'] = str(time.time())
                write_config.write(lock_file)
                # print(f'BUSY lock file created - {write_config.sections()}')
            if lock is not None and lock.locked():
                lock.release()
                # print('\tthread lock released')

            # if Modem(index).SMS.set(text=text, number=number).send(timeout=timeout):
            modem=modem.SMS.set(text=text, number=number)
            modem.send(timeout=timeout)
        except subprocess.CalledProcessError as error:
            print('catching a sent subprocess error')
            create_benchmark_file()
            raise subprocess.CalledProcessError(cmd=error.cmd, output=error.output, returncode=error.returncode)
        except Exception as error:
            create_benchmark_file()
            raise Exception(error)
        finally:
            ''' if benchmark file and limit is reached, file would be removed '''
            status, lock_type, lock_file = Deku.modem_locked(identifier=index[0], id_type=Modem.IDENTIFIERS.INDEX)

            if status and lock_type == 'BUSY':
                os.remove(lock_file)
                # print(f'modem[{identifier}] - busy lock removed')
               
        return 0

    @staticmethod
    def modem(modem_index):
        return Modem(index)


    @staticmethod
    def reset(modem_index=None):
        pass

    @staticmethod
    def stats(modem_index=None):
        pass

    @staticmethod
    def delete(sms_index, modem_index=None):
        pass

    @staticmethod
    def logs():
        pass

    @classmethod
    def __del__(cls):
        print('deleting Deku instances - should set lock files free')

    @classmethod
    def __init__(cls):
        # lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{modem.imei}.lock')
        # os.rmdir(os.path.join(os.path.dirname(__file__), 'locks', f''))
        # os.makedirs(os.path.join(os.path.dirname(__file__), 'locks', f''), exists_ok=True)
        '''
        LOAD BALANCING
        --------------
        - Check the contents of locks to make sure it's appropriate to remove the files
        - checks if file type is busy
        '''
        print('instantiated new Deku')

    @classmethod
    def __watchdog(cls):
        ''' should handle cleansing MMS messages '''

    @classmethod
    def inbound_listener(cls, modem_index):
        print('listening for incoming messages')


        ''' always running
        checks if new message from isp
        should maybe be parsed with s_layer than f_layer
        '''
        try:
            print(Modem(modem_index).SMS.list('received'))

            recv_messages = Modem(modem_index).SMS.list('received')
            for sms_index in recv_messages:
                sms=Modem.SMS(index=sms_index)
                '''
                print(f'text: {sms.text}')
                print(f'text: {sms.number}')
                '''
                ''' route messages using rabbit '''
                import pika
                fanout_channel.basic_publish(exchange='DEKU_CLUSTER', routing_key=routing_key, body=json.dumps(json_data))
        except subprocess.CalledProcessError as error:
            print(error.output)


if __name__ == "__main__":
    ''' this is the main program so everything should start from here '''
    Deku.inbound_listener(sys.argv[1])
