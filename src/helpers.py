#!/usr/bin/env python3

import common.MCCMNC as MCCMNC
from common.mmcli_python.modem import Modem

def validate_repair_request(self, number, method):
    try:
        Deku.validate_MSISDN(number)
    
    except Deku.InvalidNumber as error:
        logging.debug("invalid number, dumping message")
        self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)

    except Deku.BadFormNumber as error:
        if error.message == 'MISSING_COUNTRY_CODE':
            logging.debug("Detected missing country code, attempting to repair...")

            try:
                # TODO get country from modems
                new_number = Deku.get_modem_country_code(self.modem) + number
                Deku.validate_MSISDN(new_number)
            except Deku.InvalidNumber as error:
                logging.error("invalid number, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                raise Exception("")

            except Deku.BadFormNumber as error:
                logging.error("badly formed number, dumping message")
                self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
                raise Exception("")
            
            except Exception as error:
                logging.exception(error)
                raise error

            else:
                number = new_number
                logging.debug("Repaired successful - %s", number)
        else:
            logging.error("invalid country code, dumping message")
            self.outgoing_channel.basic_ack(delivery_tag=method.delivery_tag)
            raise Exception("")

    except Exception as error:
        logging.exception(error)
        raise error

    return number


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
