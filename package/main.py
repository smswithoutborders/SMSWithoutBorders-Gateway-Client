#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''

import os
import sys
import configparser
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
        if id_type == Modem.IDENTIFIERS.INDEX:
            ''' convert to imei '''
            identifier= Modem(identifier).imei

        lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{identifier}.lock')
        if os.path.isfile(lock_dir):
            return True
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
    def send(text, number, q_exception=None, identifier=None):
        import queue, json

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

        try:
            modem = Modem(index)

            lock_dir = os.path.join(os.path.dirname(__file__), 'locks', f'{modem.imei}.lock')

            os.mknod(lock_dir)
            if Modem(index).SMS.set(text=text, number=number).send():
                print('successfully sent...')
            else:
                print('failed to send...')
        except Exception as error:
            if q_exception is not None:
                q_exception.put(Exception(json.dumps({"msg":error.args[0], "_id":identifier})))
                return 1
            else:
                raise Exception(error)
        finally:
            os.remove(lock_dir)

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
    '''
    import sys
    # print(f"\n- isp determine: {Deku.ISP.determine(number=sys.argv[2], country='cameroon')}")
    try:
        if Deku.send(text=f'today = {datetime.now()}', number=sys.argv[2]) == 0:
            print('sms sent successfully')
    except Exception as error:
        print(error)

    '''
    # print(Modem.ISP.modems(Modems(sys.argv[1]).operator_code, sys.argv[2]))

    def usage():
        print("usage: deku [-option] [--attr] [value]")
        print('''option:
        -send (for outgoing messages)\n
        \t--text\n\t\t\tbody of the message
        \t--number\n\t\t\treceipient number
        ''')

    if len(sys.argv) < 2:
        usage()
        exit(2)

    if sys.argv[1] == '-send':
        pass
    else:
        usage()
        exit(2)

