#!/usr/bin/env python3

import phonenumbers
import common.MCCMNC as MCCMNC
from common.mmcli_python.modem import Modem
from phonenumbers import geocoder, carrier


INVALID_COUNTRY_CODE_EXCEPTION = "INVALID_COUNTRY_CODE"

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


class BadFormNumber(Exception):
    def __init__(self, number, message=None):
        self.number=number
        self.message=message or 'badly formed number'
        super().__init__(self.message)

class NoAvailableModem(Exception):
    def __init__(self, message=None):
        self.message=message or 'no available modem'
        super().__init__(self.message)

def validate_repair_request(self, MSISDN: str) -> str:
    """
    """

    try:
        validate_MSISDN(MSISDN)
    
    except InvalidNumber as error:
        raise error

    except BadFormNumber as error:
        if error.message == 'MISSING_COUNTRY_CODE':
            logging.debug("Detected missing country code, attempting to repair...")

            try:
                # TODO get country from modems
                new_MSISDN = get_modem_country_code(self.modem) + MSISDN
                validate_MSISDN(new_MSISDN)
            except InvalidNumber as error:
                raise error

            except BadFormNumber as error:
                raise error
            
            except Exception as error:
                raise error

            else:
                MSISDN = new_MSISDN
                logging.debug("Repaired successful - %s", MSISDN)
        else:
            raise Exception(INVALID_COUNTRY_CODE_EXCEPTION)

    except Exception as error:
        raise error

    return MSISDN


def get_modem_operator_name(modem:Modem)->str:
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


def get_modem_operator_country(modem:Modem) -> str:
    try:
        operator_code = modem.operator_code

        ''' requires the first 3 digits '''
        cm_op_code = int(modem.operator_code[0:3])
        if cm_op_code in MCCMNC.MCC_dict:
            operator_details = MCCMNC.MCC_dict[cm_op_code]

            return str(operator_details[0])

    except Exception as error:
        raise error

def get_modem_country_code(modem:Modem)->str:
    operator_code = modem.operator_code

    ''' requires the first 3 digits '''
    cm_op_code = int(modem.operator_code[0:3])
    if cm_op_code in MCCMNC.MCC_dict:
        operator_details = MCCMNC.MCC_dict[cm_op_code]

        return str(operator_details[1])

    return ''


def validate_MSISDN(MSISDN:str)->bool:
    try:
        _number = phonenumbers.parse(MSISDN, 'en')

        if not phonenumbers.is_valid_number(_number):
            raise InvalidNumber(number)

        return \
                phonenumbers.geocoder.description_for_number(_number, 'en'), \
                phonenumbers.carrier.name_for_number(_number, 'en')

    except phonenumbers.NumberParseException as error:
        if error.error_type == phonenumbers.NumberParseException.INVALID_COUNTRY_CODE:
            if MSISDN[0] == '+' or MSISDN[0] == '0':
                raise BadFormNumber( MSISDN, 'INVALID_COUNTRY_CODE')
            else:
                raise BadFormNumber( MSISDN, 'MISSING_COUNTRY_CODE')

        else:
            raise error

    except Exception as error:
        raise error
