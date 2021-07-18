#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import os, sys, time, queue, json
import configparser, threading
from datetime import datetime

sys.path.append(os.path.abspath(os.getcwd()))
from mmcli_python.modem import Modem

class Deku(Modem):

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
            config.read(os.path.join(os.path.dirname(__file__), 'isp_configs', 'default.ini'))

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
            config.read(os.path.join(os.path.dirname(__file__), 'isp_configs', 'operators.ini'))

            for isp in config[country]:
                if config[country][isp] == operator_code:
                    # print('modems isp found: ', isp)
                    return isp

            return None

        
    @staticmethod
    def modem_is_locked(identifier, id_type:Modem.IDENTIFIERS=Modem.IDENTIFIERS.IMEI):
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
        if os.path.isfile(lock_dir):
            print(f'{identifier}.lock exist')
            '''
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
            lock_config.read(os.path.join(os.path.dirname(__file__), 'locks', f'{identifier}.lock'))
            start_time = float(lock_config['LOCKS']['START_TIME'])
            lock_type = lock_config['LOCKS']['TYPE']

            ''' benchmark limit should come from configs 
            calculate the time difference
            '''
            ''' how long should benchmarks last before expiring '''
            benchmark_timelimit = 60
            if (time.time() - start_time ) > benchmark_timelimit and lock_type == 'BENCHMARK': #seconds
                print('\ttype = benchmark')
                ''' set the file free '''
                os.remove(lock_dir)
                print('set lock file free')
                return False
            print('\ttype = busy')
            return True
            
        print(f'{identifier} no lock file')
        return False

    @staticmethod
    def available_modem(isp=None, country=None):
        available_index=None
        indexes= Modem.list()
        # print('fetching available modems')
        for index in indexes:
            # filter for same isp
            '''
            checking operator_name is wrong... the name changes very frequently
            use operator code instead
            '''
            print(f'Modem operator code {Modem(index).operator_code}')
            # print(Deku.ISP.__dict__)
            # print(country)
            modem_isp = Deku.ISP.modems(operator_code=Modem(index).operator_code, country=country)
            print(f'modem isp {modem_isp} - {isp} = {modem_isp.lower() == isp.lower()}')

            ''' should be in setting before deciding to use isp checking here -
            credit is still a viable option '''
            if modem_isp.lower() == isp.lower():
                # check if lockfile exist for any of this modems
                if not Deku.modem_is_locked(identifier=index, id_type=Modem.IDENTIFIERS.INDEX):
                    print('modem is not locked')
                    available_index = index
                    break
                else:
                    print('modem is locked')
        return available_index

    @staticmethod
    # def send(text, number, timeout=20, q_exception:queue=None, identifier=None, t_lock:threading.Lock=None):
    def send(text, number, timeout=20, q_exception:queue=None, identifier=None, modem_locks=None):
        # TODO: 
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
        if modem_locks is not None and identifier in modem_locks and modem_locks[identifier].locked():
            print('Cannot create lock file, file begin created by another process')
            return 1

        '''
        check if modem is already locked creating busy file, else create the busy file
        '''
        modem_locks[identifier] = threading.Lock()
        modem_locks[identifier].acquire()

        print(f'new deku send request {text}, {number}')
        if text is None:
            raise Exception('text cannot be empty')
        if number is None:
            raise Exception('number cannot be empty')

        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
        country = config['ISP']['country']
        isp=Deku.ISP.determine(number=number, country=country)
        # print('isp ', isp)
        # threading.Thread.acquire(blocking)
        index= Deku.available_modem(isp=isp, country=country)


        # print('available modem with index at', index)
        lock_dir=None

        if index is None:
            msg=f'no available modem for type {isp}'
            if q_exception is not None:
                q_exception.put(Exception(json.dumps({"msg":msg, "_id":identifier})))
                return 1

            else:
                raise Exception(msg)

        lock_dir = None
        try:

            modem = Modem(index)
            lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{modem.imei}.lock')
            # os.mknod(lock_dir)
            with open(lock_dir, 'w') as lock_file:
                write_config = configparser.ConfigParser()
                write_config['LOCKS'] = {}
                write_config['LOCKS']['TYPE'] = 'BUSY'
                write_config['LOCKS']['START_TIME'] = str(time.time())
                write_config.write(lock_file)
                print('BUSY lock file created')

                if Modem(index).SMS.set(text=text, number=number).send(timeout=timeout):
                    print('successfully sent...')
                else:
                    print('failed to send...')
        except Exception as error:
            print('lock file at:', lock_dir)
            with open(lock_dir, 'w') as lock_file:
                write_config = configparser.ConfigParser()
                '''write_config.add_section('LOCKS')
                write_config.set('LOCKS', 'TYPE', 'BENCHMARK')
                write_config.set('LOCKS', 'START_TIME', str(time.time()))
                write_config.write(lock_file)'''
                write_config['LOCKS'] = {}
                write_config['LOCKS']['TYPE'] = 'BENCHMARK'
                write_config['LOCKS']['START_TIME'] = str(time.time())
                write_config.write(lock_file)
                print('BENCHMARK lock file created')

            if q_exception is not None:
                q_exception.put(Exception(json.dumps({"msg":error.args[0], "_id":identifier})))
                return 1
            else:
                raise Exception(error)
        finally:
            ''' release thread from lock '''
            modem_locks[identifier].release()
            try:
                os.remove(lock_dir)
            except Exception as error:
                # print(error)
                print(traceback.format_exc())

        return 0


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
