#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import os
import configparser
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
            print('number', number)

            for rules in config[country]:
                # print(rules)
                ''' checks if has country code '''
                for rule in config[country][rules].split(','):
                    if re.search(rule, number):
                        return rules


            return None
        
    @staticmethod
    def modem_is_locked(identifier, id_type:Modem.IDENTIFIERS=Modem.IDENTIFIERS.IMEI):
        if id_type == Modem.IDENTIFIERS.INDEX:
            ''' convert to imei '''
            identifier= Modem(identifier).imei

        # print('id ', identifier)
        # TODO:change this to use relative paths
        if os.path.isfile(f'locks/{identifier}.lock'):
            return True
        return False


    @classmethod
    def available_modem(cls):
        available_index=None
        indexes= Modem.list()
        # print(indexes)
        for index in indexes:
            # check if lockfile exist for any of this modems
            if not Deku.modem_is_locked(index, id_type=Modem.IDENTIFIERS.INDEX):
                print(f'modem[{index}] is locked ', False)
                available_index = index
                break
            print(f'modem[{index}] is locked ', True)
        return available_index

    @classmethod
    def send(cls, text, number):
        if text is None:
            raise Exception('text cannot be empty')
        if number is None:
            raise Exception('number cannot be empty')

        index=cls.available_modem()
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
            country = config['isp']['country']

            Modem(index).ISP.determine(number=number, country=country).send(text=text, number=number)
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

    # print('available modem index', Deku.available_modem())
    from datetime import datetime
    import sys
    print(f"\n- isp determine: {Deku.ISP.determine(number=sys.argv[2], country='cameroon')}")

    '''
    if Deku.send(text=f'today = {datetime.now()}', number=sys.argv[1]):
        # do something
        print('sms sent')
    else:
        # wait for a modem to free up
        # wait for a modem to become available
        print('sms failed to send')
    '''
