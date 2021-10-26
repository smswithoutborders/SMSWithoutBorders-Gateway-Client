#!/usr/bin/env python3

''' Telegram '''
from transmissionLayer_telegram import TelegramTransmissionLayer

class TransmissionLayer:
    @classmethod
    def __init__(cls):
        ''' declare your layers here '''
        cls.telegram = TelegramTransmissionLayer()

        ''' if more layers are added, they should be appended to this list '''
        cls.transmission_layers = []
        cls.transmission_layers.append(cls.telegram)

    # def send(self, data, tranmission_platform='telegram'):
    @classmethod
    def send(cls, data):
        for platform in cls.transmission_layers:
            ''' funny things are expected to happen here, 
            catch as many as possible '''
            platform.send(data)


if __name__ == "__main__":
    ''' 
    -> transmission layer has all the layers is supports imported
    -> which ever transmission layer has all the required settings gets used
    '''

    # transmissionLayer = TransmissionLayer()

    # print(tranmissionLayer.list_layers())
    ''' send is inherited from each of the layers, so the logic is based on the layer's code '''
    ''' things could happen, so have the exceptions for when they do ready '''
    TransmissionLayer().send("hello world")
