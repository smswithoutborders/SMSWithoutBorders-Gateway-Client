#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import os
from mmcli_python.modem import Modem

class Deku(Modem):
        
    @staticmethod
    def modem_is_locked(identifier, id_type:Modem.IDENTIFIERS=Modem.IDENTIFIERS.IMEI):
        if id_type == Modem.IDENTIFIERS.INDEX:
            ''' convert to imei '''
            identifier= Modem(identifier).imei

        if os.path.isfile(f'{identifier}.lock'):
            return True
        return False


    @classmethod
    def available_modem(cls):
        available_index=None
        indexes= Modem.list()
        for index in indexes:
            print('index ', index)
            # check if lockfile exist for any of this modems
            print('modem is locked ', Deku.modem_is_locked(index))
        return available_index

    @classmethod
    def send(cls, text, number):
        if text is None:
            raise Exception('text cannot be empty')
        if number is None:
            raise Exception('number cannot be empty')

        index=cls.available_modem()
        try:
            Modem(index).isp.determine(number).send(text=text, number=number)
        except Exception as error:
            raise Exception(error)

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

if __name__ == "__main__":
    # deku send --text="" --number=""
    # SEND_PERSIST=100 deku send --text="" --number=""
    # deku read
    # deku reset
    # deku stats
    # deku delete --index=#

    # https://docs.python.org/2/library/logging.handlers.html#sysloghandler
    # deku logs

    Deku.available_modem()    
    '''
    if Deku.send(text='', number=''):
        # do something
        pass
    else:
        # wait for a modem to free up
        # wait for a modem to become available
        pass
    '''
