#!/usr/bin/env python3

'''
- messages are routed using rabbitmq
- the receiver holds the routing service '''


import json
import requests
from enum import Enum
from deku import Deku

class Router(Deku):
    class Modes(Enum):
        OFFLINE='0'
        ONLINE='1'
        SWITCH='2'

    class MissingComponent(Exception):
        def __init__(self, component):
            self.component = component

    ssl = None
    # def __init__(self, cert, key):
    def __init__(self, url, priority_offline_isp, ssl=None):
        super().__init__()
        self.ssl = ssl 
        self.url = url
        self.priority_offline_isp = priority_offline_isp


    def route_offline(self, text, number):
        print('* routing offline mode')
        # print(f'\ttext-: {text}\n\tnumber-: {number}')
        ''' 
        find modems for matching isp
        send sms and fail if not delivered
        '''
        try:
            self.send(
                    text=text,
                    number=number,
                    number_isp=False,
                    isp=self.priority_offline_isp)
        except self.NoAvailableModem as error:
            raise error
        except Exception as error:
            raise error


    def route_online(self, data, protocol='GET', url=None):
        print(f"* routing online {data} {protocol}")
        results=None
        is_json=False

        try:
            json.loads(data)
            is_json=True
        except ValueError as error:
            pass

        try:
            if protocol == 'GET': 
                if is_json:
                    if self.ssl is not None:
                        results = requests.get(self.url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(self.url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.get(self.url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(self.url, data=data)


            if protocol == 'POST': 
                if is_json:
                    if self.ssl is not None:
                        results = requests.post(self.url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(self.url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.post(self.url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(self.url, data=data)

        except ConnectionError as error:
            '''
            In the event of a network problem (e.g. DNS failure, refused connection, etc), Requests will raise a ConnectionError exception.
            '''
            raise ConnectionError(error)

        except requests.Timeout as error:
            '''
            If a request times out, a Timeout exception is raised.
            '''
            raise request.Timeout(error)

        except requests.TooManyRedirects as error:
            '''
            If a request exceeds the configured number of maximum redirections, a TooManyRedirects exception is raised.
            '''
            raise requests.TooManyRedirects(error)

        return results

if __name__ == "__main__":
    data=json.dumps({"text":"Hello world", "number":"0000"})
    router = Router(url='http://localhost:6969', priority_offline_isp='orange')
    # router.route_online(data=data)
    results = router.route_online(data=data, protocol='POST')
    print(results.text, results.status_code)
