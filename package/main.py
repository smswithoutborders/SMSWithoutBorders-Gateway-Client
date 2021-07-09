#!/usr/bin/python3

'''
- making Deku and SMS manager
- Deku runs in the terminal no place else
'''


class Deku():
    @classmethod
    def available_modem(cls):
        available_index=None
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

    if Deku.send(text='', number=''):
        # do something
        pass
    else:
        # wait for a modem to free up
        # wait for a modem to become available
        pass
