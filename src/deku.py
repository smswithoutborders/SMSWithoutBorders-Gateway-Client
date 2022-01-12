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
import subprocess
import phonenumbers

from datetime import datetime
from phonenumbers import geocoder, carrier

from common.mmcli_python.modem import Modem
from common.CustomConfigParser.customconfigparser import CustomConfigParser

class Deku(Modem):

    @classmethod
    def __init__(cls, config, config_isp_default, config_isp_operators):
        cls.config = config
        cls.config_isp_operators = config_isp_operators

    class NoMatchOperator(Exception):
        def __init__(self, number, message=None):
            self.number=number
            self.message=message or 'no match operator'
            super().__init__(self.message)

    class InvalidNumber(Exception):
        def __init__(self, number, message=None):
            self.number=number
            self.message=message or 'invalid number'
            super().__init__(self.message)

    class InvalidText(Exception):
        def __init__(self, text=None, message=None):
            self.text=text
            self.message=message or 'invalid text'
            super().__init__(self.message)

    class BadFormNumber(Exception):
        def __init__(self, number, message=None):
            self.number=number
            self.message=message or 'badly formed number'
            super().__init__(self.message)

    class NoAvailableModem(Exception):
        def __init__(self, message=None):
            self.message=message or 'no available modem'
            super().__init__(self.message)

    @classmethod
    def modem_operator(cls, modem:Modem, country):
        operator_code = modem.operator_code
        for operator in cls.config_isp_operators[country]:
            if cls.config_isp_operators[country][operator].lower() == operator_code.lower():
                return operator

        return ''
        

    @classmethod
    def modem_locked(cls, modem, remove_lock=True):
        try:
            lock_type=None
            start_time=None
            modem_state_filename = os.path.join(
                    os.path.dirname(__file__), 'services/locks', f'{modem.imei}.lock')

            if os.path.isfile(modem_state_filename):
                lock_config = configparser.ConfigParser()
                lock_config.read(modem_state_filename)

                start_time = float(lock_config['LOCKS']['START_TIME'])
                lock_type = lock_config['LOCKS']['TYPE']

                ''' how long should benchmarks last before expiring '''
                benchmark_timelimit = int(cls.config['MODEMS']['failed_sleep'])

                ''' how long should benchmarks last before expiring if state is busy '''
                busy_timelimit = int(cls.config['MODEMS']['busy_benchmark_limit'])

                if remove_lock and (
                        (time.time() - start_time ) > benchmark_timelimit and \
                                (lock_type == 'FAILED' or lock_type == 'BUSY')):

                    os.remove(modem_state_filename)
                    return False, lock_type, modem_state_filename

                else:
                    return True, lock_type, modem_state_filename

        except Exception as error:
            raise error

        return False, lock_type, modem_state_filename
    
    @staticmethod
    def modem_ready(modem:Modem, index_only=False):
        try:
            if modem.state == 'disabled' or modem.state == 'idle':
                modem.enable()
            if modem.state == 'failed':
                return False
            operator_code = modem.operator_code

        except NameError as error:
            raise error
        except Exception as error:
            raise error

        if index_only:
            return modem.index in Modem.list()
        return modem.index in Modem.list() and operator_code != '--'


    @staticmethod
    def __write_lock_file__(lock_file, status):
        with open(lock_file, 'w') as fd_lock_file:
            write_config = configparser.ConfigParser()
            write_config['LOCKS'] = {}
            write_config['LOCKS']['TYPE'] = status
            write_config['LOCKS']['START_TIME'] = str(time.time())
            write_config.write(fd_lock_file)


    @classmethod
    def __change_modem_state(cls, modem_imei, state):
        lock_file = os.path.join(os.path.dirname(__file__), 
                'services/locks', f'{modem.imei}.lock')
        Deku.__write_lock_file__(lock_file, 'BUSY')


    @classmethod
    def operator_send(cls, operator_name, text, number):
        pass
    
    @classmethod
    def number_send(cls, text, number):
        pass


    @classmethod
    def modem_available(cls, modem:Modem ):
        # check modem state
        is_locked,_,__ = cls.modem_locked(modem=modem)

        return is_locked, Deku.modem_ready(modem)

    @classmethod
    def get_available_modems(cls):
        available_modems = []
        locked_modems = []
        hw_inactive_modems = []
        for modem_index in Modem.list():
            modem = Modem(index=modem_index)

            is_locked, hw_active_state = cls.modem_available( modem )

            if is_locked:
                locked_modems.append(modem)
            
            if not hw_active_state:
                hw_inactive_modems.append(state)
            
            if not is_locked and hw_active_state:
                available_modems.append(modem)

        return available_modems, locked_modems, hw_inactive_modems


    @staticmethod
    def validate_number(number):
        try:
            _number = phonenumbers.parse(number, 'en')

            if not phonenumbers.is_valid_number(_number):
                raise Deku.InvalidNumber(number)

            return \
                    phonenumbers.geocoder.description_for_number(_number, 'en'), \
                    phonenumbers.carrier.name_for_number(_number, 'en')

        except phonenumbers.NumberParseException as error:
            if error.error_type == phonenumbers.NumberParseException.INVALID_COUNTRY_CODE:
                if number[0] == '+' or number[0] == '0':
                    raise Deku.BadFormNumber( number, 'INVALID_COUNTRY_CODE')
                else:
                    raise Deku.BadFormNumber( number, 'MISSING_COUNTRY_CODE')

            else:
                raise error

        except Exception as error:
            raise error

    @classmethod
    def modem_send(cls, modem_index, text, number, timeout=20, match_operator=False):
        ''' sends through specified modem '''

        # check if modem is available
        modem = Modem(index=modem_index)
        is_locked, hw_active_state = cls.modem_available(modem)
        if is_locked or not hw_active_state:
            raise Deku.NoAvailableModem()

        # validate number
        try:
            country_code, operator_name = Deku.validate_number(number)

            if match_operator:
                logging.debug("Matching operator...")
                modem_operator = Deku.modem_operator(modem, cls.config['ISP']['country']) 
                print("modem operator:", modem_operator.lower(), 
                        " number operator", operator_name.lower())
                if operator_name.lower().find(modem_operator.lower()) < 0:
                    raise Deku.NoMatchOperator(number)

        except Deku.InvalidNumber as error:
            raise error

        except Deku.BadFormNumber as error:
            raise error

        except Exception as error:
            raise error

        # validate text
        if len(text) < 1:
            raise Deku.InvalidText('length cannot be 0')


        # send through modem
        try:
            logging.debug("Sending SMS...")
            SMS=modem.SMS.set(text=text, number=number)
            SMS.send(timeout=timeout)
            logging.debug("SENT SMS!")
        
        except subprocess.CalledProcessError as error:
            Deku.__change_modem_state(modem_imei=modem.imei, state='FAILED')

            raise subprocess.CalledProcessError(cmd=error.cmd, 
                    output=error.output, returncode=error.returncode)

        except Exception as error:
            Deku.__change_modem_state(modem_imei=modem.imei, state='FAILED')
            raise error

        finally:
            status, lock_type, lock_file = Deku.modem_locked(modem)
            logging.debug("status %s, lock_type %s, lock_file %s", 
                    status, lock_type, lock_file)

            if status and lock_type == 'BUSY':
                os.remove(lock_file)


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
