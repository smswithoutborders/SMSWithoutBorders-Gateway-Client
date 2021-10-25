#!/usr/bin/env python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import configparser, re
import os, sys, time, queue, json, traceback 
import configparser, threading
from datetime import datetime
import subprocess

# sys.path.append(os.path.abspath(os.getcwd()))
from mmcli_python.modem import Modem
from CustomConfigParser.customconfigparser import CustomConfigParser

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
        
        @classmethod
        def __init__(cls):
            try:
                cls.config = CustomConfigParser()
                cls.config_isp_default = cls.config.read('configs/isp/default.ini')
                cls.config_isp_operators = cls.config.read('configs/isp/operators.ini')
            except CustomConfigParser.NoDefaultFile as error:
                # print(traceback.format_exc())
                raise(error)
            except CustomConfigParser.ConfigFileNotFound as error:
                ''' with this implementation, it stops at the first exception - intended?? '''
                # print(traceback.format_exc())
                raise(error)
            except CustomConfigParser.ConfigFileNotInList as error:
                # print(traceback.format_exc())
                raise(error)

        @classmethod
        def determine(cls, number, country, parsed_rules=None):
            if number.find(cls.config_isp_default['country_codes'][country]) > -1:
                number= number.replace(cls.config_isp_default['country_codes'][country], '')
            # print('number', number)
            for rules in cls.config_isp_default[country]:
                # print(rules)
                ''' checks if has country code '''
                for rule in cls.config_isp_default[country][rules].split(','):
                    if re.search(rule, number):
                        return rules

            print('could not determine rule')
            return None

        @classmethod
        def modems(cls, country, operator_code):
            # print(f"determining modem's isp {country} {operator_code}")
            for isp in cls.config_isp_operators[country]:
                if cls.config_isp_operators[country][isp].lower() == operator_code.lower():
                    # print('modems isp found: ', isp)
                    return isp

            return None

        
    @classmethod
    def modem_locked(cls, identifier, id_type:Modem.IDENTIFIERS=Modem.IDENTIFIERS.IMEI, remove_lock=True):
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

        lock_dir = os.path.join(os.path.dirname(__file__), 'service_files/locks', f'{identifier}.lock')
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

            start_time = float(lock_config['LOCKS']['START_TIME'])
            lock_type = lock_config['LOCKS']['TYPE']

            ''' benchmark limit should come from configs 
            calculate the time difference
            '''
            ''' how long should benchmarks last before expiring '''
            benchmark_timelimit = int(cls.config['MODEMS']['failed_sleep'])

            ''' how long should benchmarks last before expiring if state is busy '''
            busy_timelimit = int(cls.config['MODEMS']['busy_benchmark_limit'])

            # print(f'lt: {lock_type}\nnow: {time.time()}\nstart_time: {start_time}\ndiff: {time.time() - start_time}')
            if remove_lock and ((time.time() - start_time ) > benchmark_timelimit and lock_type == 'BENCHMARK') or ((time.time() - start_time ) > busy_timelimit and lock_type == 'BUSY'): #seconds
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
            modem = Modem(modem_index)
            '''
            if modem.state != 'registered':
                modem.enable()
            '''
            if modem.state == 'disabled':
                modem.enable()
            moc = modem.operator_code
        except NameError as error:
            # raise Exception(error)
            return False
        except Exception as error:
            raise Exception(error)

        # print('moc:', moc)
        return modem_index in Modem.list() and (moc != '--' and moc is not None)

    @classmethod
    def status(cls):
        ''' should be used from the Deku lib '''
        indexes=cls.modems_ready()
        messages=[]
        for index in indexes:
            modem=Modem(index)
            message=f'====Modem({modem.imei})====\n- index={index}\n- state={modem.state}\n- model={modem.model}\n- dbus_path={modem.dbus_path}\n- power_state={modem.power_state}\n- operator_code={modem.operator_code}\n- operator_name={modem.operator_name}\n\n'
            messages.append(message)


        return messages

    @staticmethod
    def modems_ready(isp=None, country=None, m_index=None, remove_lock=False, ignore_lock=False):
        available_indexes=[]
        # print('fetching available modems')

        indexes=[]
        if m_index is not None:
            indexes.append(m_index)
        else:
            indexes= Modem.list()

        for _m_index in indexes:
            # filter for same isp
            '''
            checking operator_name is wrong... the name changes very frequently
            use operator code instead
            '''
            # print(f'Modem operator code {Modem(m_index).operator_code}')
            # print(Deku.ISP.__dict__)
            # print(country)

            locked_state, lock_type, lock_file = Deku.modem_locked(Modem(_m_index).imei, remove_lock=remove_lock)

            if not ignore_lock and locked_state:
                # return available_indexes
                continue

            ''' should be in setting before deciding to use isp checking here -
            credit is still a viable option '''
            if isp is None:
                ''' when sending, modem can't take another job unless faulty node 
                if not Deku.modem_locked(identifier=index, id_type=Modem.IDENTIFIERS.INDEX)[0]:
                    # print('modem is not locked')
                    available_indexes.append(index)
                '''
                if Deku.modem_ready(_m_index):
                    available_indexes.append(_m_index)

            else:
                if country is None:
                    raise Exception('country cannot be None')
                modem_isp = Deku.ISP.modems(operator_code=Modem(_m_index).operator_code, country=country)
                if isp == modem_isp and Deku.modem_ready(_m_index):
                    available_indexes.append(_m_index)

        return available_indexes


    @classmethod
    # def send(text, number, timeout=20, q_exception:queue=None, identifier=None, t_lock:threading.Lock=None):
    def send(cls, text, number, timeout=20, number_isp=True, m_index=None, q_exception:queue=None, identifier=None, lock:threading.Lock=None):
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


        ''' determines if to check the isp of the number - best used without node '''
        isp=None
        index=[]
        if m_index is None:
            if number_isp:
                """
                config = configparser.ConfigParser()
                config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
                """
                country = cls.config['ISP']['country']
                print(f'number {number}, country {country}')
                isp=Deku.ISP.determine(number=number, country=country)

                if isp is None:
                    '''invalid number, should completely delete this from queueu'''
                    raise Deku.InvalidNumber(number, 'invalid number')

                index= Deku.modems_ready(isp=isp, country=country)
            else:
                index=Deku.modems_ready()
        else:
            index=Deku.modems_ready(m_index=m_index)
        print('ready index:', index)

        # print('available modem with index at', index)
        lock_dir=None

        if len(index) < 1:
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
        ''' use paths from config '''
        ''' user may not change the default value so relative paths should be used in configs '''
        lock_dir = os.path.join(os.path.dirname(__file__), 'service_files/locks', f'{modem.imei}.lock')
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
            # print('catching a sent subprocess error')
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
        return Modem(modem_index)

    @classmethod
    def __init__(cls):
        ''' test deps for config files '''
        try:
            cls.ISP()

            cls.configreader=CustomConfigParser()
            cls.config=cls.configreader.read('configs/config.ini')
            # print('instantiated new Deku')
        except CustomConfigParser.NoDefaultFile as error:
            # print(traceback.format_exc())
            raise(error)
        except CustomConfigParser.ConfigFileNotFound as error:
            ''' with this implementation, it stops at the first exception - intended?? '''
            raise(error)
        except CustomConfigParser.ConfigFileNotInList as error:
            raise(error)

    @classmethod
    def cli_parse_ussd(cls, modem_index, command):
        # parse it first
        # *158*0#|1
        command = command.split('|')
        ussd_output=[]
        try:
            output=[command[0], cls.USSD(Modem(modem_index)).initiate(command[0])]
            # print(output)
            ussd_output.append(output)
            for cmd in command[1:]:
                output=[cmd, cls.USSD(Modem(modem_index)).respond(cmd)]
                # print(output)
                ussd_output.append(output)
        except cls.USSD.UnknownError as error:
            raise(error)
        except cls.USSD.ActiveSession as error:
            # raise(error)
            print("* active sessions, cancelling sessions")
            cls.USSD.cancel()
        except cls.USSD.CannotInitiateUSSD as error:
            # print("- output:", error.output)
            # print("- command:", error.command)
            raise(error)
        except subprocess.CalledProcessError as error:
            # print("::Error>", error.cmd, error.output)
            # print(traceback.format_exc())
            # print(error.output)
            # error.output = ussd_output
            raise(error)

        return ussd_output

    @classmethod
    def cli_parse_labels(cls, modem_index, label):

        def execute_command(command):
            print('* executing label command', command)
            command=command.split(' ')
            
            if command[0] == 'ussd':
                try:
                    return cls.cli_parse_ussd(modem_index, command[1])
                except cls.USSD.CannotInitiateUSSD as error:
                    raise(error)
                except subprocess.CalledProcessError as error:
                    # print(error.output)
                    # print(error.output)
                    raise(error)
            else:
                print("** unknown label command requested")

            return None

        country=cls.config['ISP']['country']
        modem_isp = cls.ISP.modems(operator_code=Modem(modem_index).operator_code, country=country)
        print("modem isp:", modem_isp)
        if modem_isp is None:
            print("* cannot determine modem's isp")
            return None

        ''' check of for labels that match the requested labels, 
        then execute for the matching isp for that label '''
        path_label = os.path.join(os.path.dirname(__file__), 'extensions', f'labels.ini')

        label_config = configparser.ConfigParser()
        label_config.read(path_label)

        if label in label_config and modem_isp in label_config[label]:
            ''' parse the commands for their correspondences '''
            return execute_command(label_config[label][modem_isp])
        else:
            print(f"** no label({label}) in labels file")


if __name__ == "__main__":
    ''' should use command line arg parser here '''
    modem_index=None
    ussd_command=None
    label_command=None
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        # print('arg:', arg)
        if arg == '--modem' or arg == '-m':
            modem_index = sys.argv[i+1]
            # i += 1
        elif arg == '--ussd':
            ussd_command = sys.argv[i+1]
            # i += 1
        elif arg == '--ussd-cancel':
            ussd_command = arg
        elif arg == '--label':
            label_command = sys.argv[i+1]
            # i += 1

    if modem_index == None:
        print("usage: --[modem_index] --[option] [value]")
        exit(1)


    if ussd_command is not None:
        if ussd_command == '--ussd-cancel':
            print("* cancelling USSD command...")
            try:
                Modem(modem_index).USSD.cancel()
            except Deku.USSD.UnknownError as error:
                print("USSD error:", str(error.output))
                exit(1)
        else:
            print(f"* Dailing USSD - {ussd_command}")
            ussd_output=Deku.cli_parse_ussd(modem_index, ussd_command)
            print(ussd_output)

    elif label_command is not None:
        print(f"* Executing label command - {label_command}")
        try:
            label_output=Deku().cli_parse_labels(modem_index, label_command)
        except Deku.USSD.CannotInitiateUSSD as error:
            # print(error.output)
            print("USSD error:", str(error.output))
            # raise(error)
            exit(1)
        else:
            print(label_output)

    exit(0)
