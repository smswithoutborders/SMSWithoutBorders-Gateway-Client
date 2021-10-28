#!/usr/bin/env python3

'''
- messages are routed using rabbitmq
- the receiver holds the routing service
'''


import requests

class Router:
    ssl = None
    # def __init__(self, cert, key):
    def __init__(self, url=router_url, priority_offline_isp, ssl=None)
        self.ssl = ssl
        self.url = url
        self.priority_offline_isp = priority_offline_isp


    def route_offline(self, text, number):
        print('* routing offline mode')
        print(f'\ttext-: {text}\n\tnumber-: {number}')


    def route_online(self, data, protocol='GET', url=None):
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
                        results = requests.get(url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.get(url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.get(url, data=data)


            if protocol == 'POST': 
                if is_json:
                    if self.ssl is not None:
                        results = requests.post(url, json=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(url, json=data)
                else:
                    if self.ssl is not None:
                        results = requests.post(url, data=data, verify=True, cert=ssl)
                    else:
                        results = requests.post(url, data=data)

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
    router = Router(url='http://localhost', priority_offline_isp='orange')
    router.route(data=data)
    router.route(data=data, protocol='POST')
