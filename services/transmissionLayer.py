#!/usr/bin/env python3

''' Telegram '''
from transmissionLayer_telegram import TelegramTransmissionLayer


class TransmissionLayer:
    def __init__(self):
        ''' declare your layers here '''
        self.telegram = TelegramTransmissionLayer()

        ''' if more layers are added, they should be appended to this list '''
        self.transmission_layers = []
        self.transmission_layers.append(self.telegram)

    # def send(self, data, tranmission_platform='telegram'):
    def send(self, data):
        for platform in self.transmission_layers:
            ''' funny things are expected to happen here, 
            catch as many as possible '''
            platform.send(data)


if __name__ == "__main__":
    ''' 
    -> transmission layer has all the layers is supports imported
    -> which ever transmission layer has all the required settings gets used
    '''

    transmissionLayer = TransmissionLayer()

    # print(tranmissionLayer.list_layers())
    ''' send is inherited from each of the layers, so the logic is based on the layer's code '''
    ''' things could happen, so have the exceptions for when they do ready '''
    transmissionLayer.send("hello world")
