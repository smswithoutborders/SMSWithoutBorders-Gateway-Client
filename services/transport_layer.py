#!/usr/bin/env python3

class TransportLayer:

    class Protocols(Enum):
        SMS=auto()
        EMAIL=auto()
        TELEGRAM=auto()

    def __init__(self, protocol:Protocols):
        self.protocol = protocol

    def broadcast(self, message):
        if self.protocol == Protocols.TELEGRAM:
            telegram.broadcast(message)

    

if __name__ == "__main__":
    ''' local_db = list of numbers which are talking with the telegram bot '''
    telegram = Telegram(local_db)
