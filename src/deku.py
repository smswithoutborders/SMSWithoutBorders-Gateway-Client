#!/usr/bin/env python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import configparser
import re
import os 
import sys 
import time 
import queue 
import json
import traceback 
import logging
import argparse
import configparser, threading
from datetime import datetime
import subprocess

from common.mmcli_python.modem import Modem
from common.CustomConfigParser.customconfigparser import CustomConfigParser

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

    class ISP:
        @classmethod
        def __init__(cls, config_isp_default, config_isp_operators):
            cls.config_isp_default = config_isp_default
            cls.config_isp_operators = config_isp_operators

        @classmethod
        def determine(cls, number, country, parsed_rules=None):
            if number.find(cls.config_isp_default['country_codes'][country]) > -1:
                number= number.replace(cls.config_isp_default['country_codes'][country], '')
            for rules in cls.config_isp_default[country]:
                for rule in cls.config_isp_default[country][rules].split(','):
                    if re.search(rule, number):
                        return rules

            logging.error('could not determine rule')
            return None

        @classmethod
        def modems(cls, country, operator_code):
            for isp in cls.config_isp_operators[country]:
                if cls.config_isp_operators[country][isp].lower() == operator_code.lower():
                    return isp
            return None

        
    @classmethod
    def modem_locked(cls, modem_index, remove_lock=True):
        imei= Modem(modem_index).imei
        lock_dir = os.path.join(os.path.dirname(__file__), 'services/locks', f'{imei}.lock')

        lock_type=None
        start_time=None
        if os.path.isfile(lock_dir):
            lock_config = configparser.ConfigParser()
            lock_config.read(lock_dir)

            start_time = float(lock_config['LOCKS']['START_TIME'])
            lock_type = lock_config['LOCKS']['TYPE']

            ''' how long should benchmarks last before expiring '''
            benchmark_timelimit = int(cls.config['MODEMS']['failed_sleep'])

            ''' how long should benchmarks last before expiring if state is busy '''
            busy_timelimit = int(cls.config['MODEMS']['busy_benchmark_limit'])

            if remove_lock and \
                    (((time.time() - start_time ) > benchmark_timelimit and lock_type == 'FAILED') \
                    or ((time.time() - start_time ) > busy_timelimit and lock_type == 'BUSY')):
                os.remove(lock_dir)
                return False, lock_type, lock_dir
            return True, lock_type, lock_dir
            
        return False, lock_type, lock_dir
    
    @staticmethod
    def modem_ready(modem_index):
        try:
            modem = Modem(modem_index)
            if modem.state == 'disabled':
                modem.enable()
            operator_code = modem.operator_code
        except NameError as error:
            raise(error)
        except Exception as error:
            raise(error)

        return modem_index in Modem.list() and operator_code != '--'
    
    @staticmethod
    def state():
        try:
            command = ['systemctl', 'is-active', 'deku_cluster.service']
            systemd_output = subprocess.check_output(
                    command, stderr=subprocess.STDOUT).decode('unicode_escape')
            return systemd_output
        except Exception as error:
            raise error


    @classmethod
    def status(cls):
        indexes=cls.modems_ready()
        messages=[]
        for index in indexes:
            modem=Modem(index)
            message=f'====Modem({modem.imei})====\n' + \
                    f'- index={index}\n' + \
                    f'- state={modem.state}\n' + \
                    f'- model={modem.model}\n' + \
                    f'- dbus_path={modem.dbus_path}\n' + \
                    f'- power_state={modem.power_state}\n' + \
                    f'- operator_code={modem.operator_code}\n' + \
                    f'- operator_name={modem.operator_name}\n'
            messages.append(message)
        return messages

    @staticmethod
    def modems_ready(isp=None, country=None, modem_index=None, remove_lock=False, ignore_lock=False):
        available_indexes=[]
        indexes=[]
        locked_indexes=[]

        if modem_index is not None:
            indexes.append(modem_index)
        else:
            indexes= Modem.list()

        for _modem_index in indexes:
            locked_state, lock_type, lock_file = Deku.modem_locked(
                    _modem_index, remove_lock=remove_lock)

            if not ignore_lock and locked_state:
                locked_indexes.append(_modem_index)
                continue

            if isp is None:
                if Deku.modem_ready(_modem_index):
                    available_indexes.append(_modem_index)
            else:
                if country is None:
                    raise Exception('country cannot be None')
                modem_isp = Deku.ISP.modems(
                        operator_code=Modem(_modem_index).operator_code, country=country)
                if isp == modem_isp and Deku.modem_ready(_modem_index):
                    available_indexes.append(_modem_index)

        return available_indexes, locked_indexes


    @classmethod
    def get_available_modems(cls, isp=None, modem_index=None, number=None, remove_lock=False, 
            number_isp=False):

        country = cls.config['ISP']['country']
        if modem_index is None: # modem is not specified - search for available modem with other filters

            if isp is not None: # check if modem for required isp is available
                available_indexes, locked_indexes = \
                        Deku.modems_ready(isp=isp, country=country, remove_lock=remove_lock)
                return available_indexes

            elif number_isp: # check if modem for number's isp is available
                isp=Deku.ISP.determine(number=number, country=country)

                if isp is None:
                    raise Deku.InvalidNumber(number, 'invalid number')

                available_indexes, locked_indexes = \
                        Deku.modems_ready(isp=isp, country=country, remove_lock=remove_lock)
                return available_indexes
            else:
                available_indexes, locked_indexes = Deku.modems_ready()
                return available_indexes
        else:
            if number_isp: # check if modem for number's isp is available
                isp=Deku.ISP.determine(number=number, country=country)

                if isp is None:
                    raise Deku.InvalidNumber(number, 'invalid number')

                available_indexes, locked_indexes = \
                        Deku.modems_ready(isp=isp, country=country, remove_lock=remove_lock)

                if modem_index in available_indexes:
                    return available_indexes

            else:
                available_indexes, locked_indexes = \
                        Deku.modems_ready(modem_index=modem_index, remove_lock=remove_lock)
            return available_indexes
            
        return None


    @staticmethod
    def write_lock_file(lock_file, status):
        with open(lock_file, 'w') as fd_lock_file:
            write_config = configparser.ConfigParser()
            write_config['LOCKS'] = {}
            write_config['LOCKS']['TYPE'] = status
            write_config['LOCKS']['START_TIME'] = str(time.time())
            write_config.write(fd_lock_file)


    @classmethod
    def send(cls, text, number, timeout=20, number_isp=True, 
            modem_index=None, remove_lock=True, ignore_lock=False, isp=None):
        logging.debug("+ text: %s\n+ number: %s", text, number)

        if text is None:
            raise Exception('text cannot be empty')
        if number is None:
            raise Exception('number cannot be empty')
        
        try:
            index = cls.get_available_modems(isp=isp, modem_index=modem_index, 
                    number=number, remove_lock=remove_lock, number_isp=number_isp)
        except Deku.InvalidNumber as error:
            raise error
        logging.debug('ready indexes %s', index)

        if len(index) < 1:
            msg = f"No available modem for type {isp}"
            raise Deku.NoAvailableModem(msg)

        modem_index=index[0] #TODO use better criteria for filtering, maybe signal strength
        modem = Modem(modem_index)

        try:
            lock_file = os.path.join(os.path.dirname(__file__), 
                    'services/locks', f'{modem.imei}.lock')
            Deku.write_lock_file(lock_file, 'BUSY')

            modem=modem.SMS.set(text=text, number=number)
            modem.send(timeout=timeout)
        except subprocess.CalledProcessError as error:
            Deku.write_lock_file(lock_file, 'FAILED')
            raise subprocess.CalledProcessError(cmd=error.cmd, 
                    output=error.output, returncode=error.returncode)
        except Exception as error:
            Deku.write_lock_file(lock_file, 'FAILED')
            raise(error)
        finally:
            status, lock_type, lock_file = Deku.modem_locked(modem_index)
            logging.debug("status %s, lock_type %s, lock_file %s", 
                    status, lock_type, lock_file)

            if status and lock_type == 'BUSY':
                os.remove(lock_file)
               
        return 0

    @staticmethod
    def modem(modem_index):
        return Modem(modem_index)

    @classmethod
    def __init__(cls, config, config_isp_default, config_isp_operators):
        cls.ISP(config_isp_default=config_isp_default, 
                config_isp_operators=config_isp_operators)

        cls.config = config

    @classmethod
    def cli_parse_ussd(cls, modem_index, command):
        command = command.split('|')
        ussd_output=[]
        try:
            output=[command[0], cls.USSD(Modem(modem_index)).initiate(command[0])]
            ussd_output.append(output)
            for cmd in command[1:]:
                output=[cmd, cls.USSD(Modem(modem_index)).respond(cmd)]
                ussd_output.append(output)
        except cls.USSD.UnknownError as error:
            raise(error)
        except cls.USSD.ActiveSession as error:
            try:
                cls.USSD.cancel()
                ussd_output = cls.cli_parse_ussd(modem_index, command)
                logging.debug("ussd cancel output: %s,", ussd_output)
            except Exception as error:
                raise(error)
        except cls.USSD.CannotInitiateUSSD as error:
            raise(error)
        except subprocess.CalledProcessError as error:
            raise(error)

        return ussd_output

    @classmethod
    def cli_parse_labels(cls, modem_index, label):
        def execute_command(command):
            command=command.split(' ')
            if command[0] == 'ussd':
                try:
                    return cls.cli_parse_ussd(modem_index, command[1])
                except cls.USSD.CannotInitiateUSSD as error:
                    raise(error)
                except subprocess.CalledProcessError as error:
                    raise(error)
            else:
                logging.warning("unknown command requested %s", command[0])
            return None

        country=cls.config['ISP']['country']
        modem_isp = cls.ISP.modems(
                operator_code=Modem(modem_index).operator_code, 
                country=country)

        if modem_isp is None:
            logging.error("cannot determine modem's isp")
            return None

        path_label = os.path.join(os.path.dirname(__file__), 'extensions', f'labels.ini')

        label_config = configparser.ConfigParser()
        label_config.read(path_label)

        if label in label_config and modem_isp in label_config[label]:
            return execute_command(label_config[label][modem_isp])
        else:
            logging.warning("label not found - %s", label)
            return None

if __name__ == "__main__":
    ''' should use command line arg parser here '''
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument(
            '-m', '--modem', 
            nargs = 1)

    parser.add_argument("-u", "--ussd", 
            nargs = 1,
            help = '"*155#|1|1"')

    parser.add_argument("-uc", "--ussd-cancel", 
            help='')

    parser.add_argument("-l", "--label", 
            nargs = 1,
            help='"*155#|1|1"')

    parser.add_argument("-s", "--sms", 
            nargs = 2,
            help='-s [phone number] [text]')

    args = parser.parse_args()

    try:
        configreader=CustomConfigParser(os.path.join(os.path.dirname(__file__), '..', ''))
        config=configreader.read(".configs/config.ini")
        config_isp_default = configreader.read('.configs/isp/default.ini')
        config_isp_operators = configreader.read('.configs/isp/operators.ini')

    except Exception as error:
        logging.critical(traceback.format_exc())

    modem_index=None
    if args.modem == None:
        print(parser.print_help())
    else:
        modem_index = args.modem[0]
        Deku(config, config_isp_default, config_isp_operators)

        if args.ussd is not None:
            ussd = args.ussd[0]
            ussd_output=Deku.cli_parse_ussd(modem_index, ussd)
            print(ussd_output)

        elif args.ussd_cancel is not None:
            try:
                Modem(modem_index).USSD.cancel()
            except Deku.USSD.UnknownError as error:
                exit(1)

        elif args.label is not None:
            label = args.label[0]
            try:
                label_output=Deku().cli_parse_labels(modem_index, label)
                print(label_output)
            except Deku.USSD.CannotInitiateUSSD as error:
                print("USSD error:", str(error.output))
                exit(1)

        elif args.sms is not None:
            sms_number = args.sms[0]
            sms_text = args.sms[1]
            # print(args.sms)
            try:
                sms_output=Deku.send(text=sms_text, number=sms_number, modem_index=modem_index)
            except Exception as error:
                print(traceback.format_exc())
                exit(1)
