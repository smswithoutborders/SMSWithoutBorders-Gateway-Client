#!/usr/bin/env python3

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

import common.MCCMNC as MCCMNC

class Deku(Modem):

    def __init__(self, modem:Modem=None)->None:
        self.modem = modem

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
    def get_modem_operator_name(cls, modem:Modem)->str:
        operator_code = modem.operator_code

        ''' requires the first 3 digits '''
        cm_op_code = (int(modem.operator_code[0:3]), int(modem.operator_code[-1]))
        if cm_op_code in MCCMNC.MNC_dict:
            operator_details = MCCMNC.MNC_dict[cm_op_code]

            if operator_details[0] == int(modem.operator_code):
                operator_name = str(operator_details[1])
                # logging.debug("%s", operator_name)

                return operator_name

        return ''

    @classmethod
    def get_modem_operator_country(cls, modem:Modem) -> str:
        try:
            operator_code = modem.operator_code

            ''' requires the first 3 digits '''
            cm_op_code = int(modem.operator_code[0:3])
            if cm_op_code in MCCMNC.MCC_dict:
                operator_details = MCCMNC.MCC_dict[cm_op_code]

                return str(operator_details[0])

        except Exception as error:
            raise error

    @classmethod
    def get_modem_country_code(cls, modem:Modem)->str:
        operator_code = modem.operator_code

        ''' requires the first 3 digits '''
        cm_op_code = int(modem.operator_code[0:3])
        if cm_op_code in MCCMNC.MCC_dict:
            operator_details = MCCMNC.MCC_dict[cm_op_code]

            return str(operator_details[1])

        return ''

    def modem_locked(self, remove_lock=True):
        try:
            lock_type=None
            start_time=None
            modem_state_filename = os.path.join(
                    os.path.dirname(__file__), 
                    'services/locks', f'{self.modem.imei}.lock')

            if os.path.isfile(modem_state_filename):
                lock_config = configparser.ConfigParser()
                lock_config.read(modem_state_filename)

                start_time = float(lock_config['LOCKS']['START_TIME'])
                lock_type = lock_config['LOCKS']['TYPE']

                ''' how long should benchmarks last before expiring '''
                # benchmark_timelimit = int(cls.config['MODEMS']['failed_sleep'])
                # benchmark_timelimit = cls.daemon_sleep_time
                benchmark_timelimit = 20

                ''' how long should benchmarks last before expiring if state is busy '''
                # busy_timelimit = int(cls.config['MODEMS']['busy_benchmark_limit'])
                # busy_timelimit = cls.daemon_busy_timeout
                busy_timelimit = 30

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
    
    def modem_ready(self, index_only=False):
        try:
            if self.modem.state == 'disabled' or self.modem.state == 'idle':
                self.modem.enable()
            if self.modem.state == 'failed':
                return False
            operator_code = self.modem.operator_code

        except NameError as error:
            raise error
        except Exception as error:
            raise error

        if index_only:
            return self.modem.index in self.modem.list()
        return self.modem.index in self.modem.list() and operator_code != '--'


    def __write_lock_file__(self,lock_file, status):
        with open(lock_file, 'w') as fd_lock_file:
            write_config = configparser.ConfigParser()
            write_config['LOCKS'] = {}
            write_config['LOCKS']['TYPE'] = status
            write_config['LOCKS']['START_TIME'] = str(time.time())
            write_config.write(fd_lock_file)


    def __change_modem_state(self, state):
        lock_file = os.path.join(os.path.dirname(__file__), 
                'services/locks', f'{self.modem.imei}.lock')
        self.__write_lock_file__(lock_file, state)

    def modem_available(self):
        is_locked,_,__ = self.modem_locked()

        return is_locked, self.modem_ready()

    @classmethod
    def get_available_modems(cls):
        available_modems = []
        locked_modems = []
        hw_inactive_modems = []

        for modem_index in Modem.list():
            try:
                modem = Modem(index=modem_index)

                deku = Deku(modem=modem)
                is_locked, hw_active_state = deku.modem_available()

                if is_locked:
                    locked_modems.append(modem)
                
                if not hw_active_state:
                    hw_inactive_modems.append(modem)
                
                if not is_locked and hw_active_state:
                    available_modems.append(modem)
            except Exception as error:
                logging.exception(error)

        return available_modems, locked_modems, hw_inactive_modems


    @staticmethod
    def validate_MSISDN(MSISDN:str)->bool:
        try:
            _number = phonenumbers.parse(MSISDN, 'en')

            if not phonenumbers.is_valid_number(_number):
                raise Deku.InvalidNumber(number)

            return \
                    phonenumbers.geocoder.description_for_number(_number, 'en'), \
                    phonenumbers.carrier.name_for_number(_number, 'en')

        except phonenumbers.NumberParseException as error:
            if error.error_type == phonenumbers.NumberParseException.INVALID_COUNTRY_CODE:
                if MSISDN[0] == '+' or MSISDN[0] == '0':
                    raise Deku.BadFormNumber( MSISDN, 'INVALID_COUNTRY_CODE')
                else:
                    raise Deku.BadFormNumber( MSISDN, 'MISSING_COUNTRY_CODE')

            else:
                raise error

        except Exception as error:
            raise error

    def modem_send(self,
            text:str, 
            number:int, 
            timeout:int=20, 
            force:bool=False,
            match_operator:bool=False)->None:
        """Send out SMS through specified modem.

            Args:
                modem (Modem): The :cls:Modem for outgoing SMS.
                text (str): Text to be sent via SMS.
                number (str): Number of SMS reciepient.
                timeout (int): How long sending daemon should request to send 
                before declaring a failure to send.
                match_operator (bool): If True Modem's operator must match the
                number's operator, else it fails to send
        """

        if not force:
            is_locked, hw_active_state = self.modem_available()
            if is_locked or not hw_active_state:
                raise Deku.NoAvailableModem()
        else:
            logging.debug("Using force not checking for locks")

        # validate number
        try:
            if match_operator:
                country, operator_name = Deku.validate_MSISDN(number)
                logging.debug("Matching operator...")
                modem_operator = Deku.get_modem_operator_name(self.modem)
                logging.debug("operator name: %s, modem operator: %s", 
                        operator_name, modem_operator)
                if not operator_name == modem_operator:
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
            sms=self.modem.sms.set(text=text, number=number)

            self.__change_modem_state(state='BUSY')
            sms.send(timeout=timeout)
            logging.debug("SENT SMS!")
        
        except subprocess.CalledProcessError as error:
            self.__change_modem_state(state='FAILED')

            '''
            raise subprocess.CalledProcessError(cmd=error.cmd, 
                    output=error.output, returncode=error.returncode)
            '''
            # logging.exception(error)
            logging.debug("%s", error.output)
            raise error

        except Exception as error:
            self.__change_modem_state(state='FAILED')
            raise error

        finally:
            status, lock_type, lock_file = self.modem_locked()
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
